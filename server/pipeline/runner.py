import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scanpy as sc
import seaborn as sns
import umap.umap_ as umap
from gseapy import enrichr
from gseapy.plot import barplot, dotplot
from scipy.stats import ttest_ind  # t-test
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests  # FDR p-value

# from statsmodels.stats.multitest import fdrcorrection

#configuration
##pipeline/runner.py
##data/xxx.csv
BASE_DIR = Path(__file__).parent.parent.resolve()  # server/pipeline -> server
DATA_DIR = BASE_DIR / 'data'
RESULT_DIR = BASE_DIR / 'results'
RESULT_DIR.mkdir(exist_ok=True, parents=True) #if not make a dir, avoid error

# EXPR_FILE = "../data/GSE138852_pseudobulk_astro_counts.csv"
# META_FILE = "../data/GSE138852_pseudobulk_astro_metadata.csv"

#loop the dir and take out the target file
expr_files = [f for f in DATA_DIR.iterdir() if f.is_file() and '__expr' in f.name.lower() and f.suffix in ['.csv', '.tsv']]
cov_files  = [f for f in DATA_DIR.iterdir() if f.is_file() and '__cov'  in f.name.lower() and f.suffix in ['.csv', '.tsv']]


if not expr_files:
    print('Error: No expression file with "__expr" found in ./data')
    sys.exit(1)
if not cov_files:
    print('Error: No covariate file with "__cov" found in ./data')
    sys.exit(1)

# Use the first match
EXPR_FILE = expr_files[0]
META_FILE = cov_files[0]

OUTPUT_DEG_CSV = f"{RESULT_DIR}/DEG_df.csv"
AD_RELEVANT_GENES = ["APOE", "CLU", "TREM2", "BIN1", "PICALM", 
                    "MAPT", "PSEN1", "PSEN2", "APP", "CR1"]


#expression matrix: genes VS samples_id
def load_expression_data(expr_file: str) -> pd.DataFrame: #type hints
    """Load and preprocess expression table"""
    if not os.path.exists(expr_file):
        raise FileNotFoundError(f"file not found: {expr_file}")
    df = pd.read_csv(expr_file, index_col=0)
    df = df.dropna(how='any') #dropna row
    print(f" Expression matrix loaded. Shape: {df.shape}")
    return df

#meta data: samples_id VS labels - AD and Health group
def load_metadata(meta_file: str) -> pd.DataFrame:
    """Load and preprocess metadata table"""
    if not os.path.exists(meta_file):
        raise FileNotFoundError(f"file not found: {meta_file}")
    df = pd.read_csv(meta_file, index_col=0)
    # df['batchCond'] = df['batchCond'].str.upper() #consistent uppercase
    df = df.dropna(how='any') #dropna row
    print(f" Metadata loaded. Shape: {df.shape}")
    return df


#QC
def scanpy_preprocess(expr_df: pd.DataFrame, meta_df: pd.DataFrame, scale_factor=10000):
    """
    Input: dfs -> Output: processed dfs
    """

    # --- 1. Transpose expression (genes x cells → cells x genes) ---
    expr_df = expr_df.T

    #Check duplicated reads
    if expr_df.index.duplicated().any():
        dup_rows = expr_df.index[expr_df.index.duplicated()].tolist()
        print(f"Warning: Found duplicated row names: {dup_rows}")
        raise ValueError("Duplicated sample IDs found in expression data.")
    else:
        print("No duplicated sample IDs found after transposing.")
    assert expr_df.shape[0] == meta_df.shape[0], "Cell IDs must match"

    # --- 2. Create AnnData object ---
    #? Parse to adata & adata.obs objects for more convenient data handling
    adata = sc.AnnData(X=expr_df)
    adata = adata.copy()
    adata.obs = meta_df.copy()
    adata.obs["oupSample.batchCond"] = adata.obs["oupSample.batchCond"].astype("category")

    # --- 3. Filter cells (5% ~ 95% of gene count and RNA count) ---
    #set qc filter
    sc.pp.calculate_qc_metrics(adata, inplace=True)
    min_genes = np.percentile(adata.obs["n_genes_by_counts"], 5)
    max_genes = np.percentile(adata.obs["n_genes_by_counts"], 95)
    min_counts = np.percentile(adata.obs["total_counts"], 5)
    max_counts = np.percentile(adata.obs["total_counts"], 95)

    adata = adata[
        (adata.obs["n_genes_by_counts"] >= min_genes) &
        (adata.obs["n_genes_by_counts"] <= max_genes) &
        (adata.obs["total_counts"] >= min_counts) &
        (adata.obs["total_counts"] <= max_counts)
    ].copy()
    print(f"✅ After cell filtering → shape: {adata.shape}")

    # --- 5. Filter genes ---
    # 1. remove genes with all 0s
    # 2. keep genes expressed in ≥10 cells with ≥2 counts
    gene_filter = np.array((adata.X >= 2).sum(axis=0)).flatten() >= 10
    adata = adata[:, gene_filter]
    print(f"✅ After gene filtering → shape: {adata.shape}")

    # --- 6. Normalisation + log1p ---
    sc.pp.normalize_total(adata, target_sum=scale_factor)
    sc.pp.log1p(adata)
    print("✅ Done normalisation and log1p")

    # --- 7. Convert back to DataFrame ---
    expr_df_processed = pd.DataFrame(adata.X,
                                     index=adata.obs_names,
                                     columns=adata.var_names)

    meta_df_processed = adata.obs.copy()

    return expr_df_processed, meta_df_processed, adata, adata.obs

#Differential expressed genes scanpy
def calculate_deg_scanpy_df(expr_df: pd.DataFrame, meta_df: pd.DataFrame) -> pd.DataFrame:
    """To perform DE analysis using t-test and log2 fold change"""

    # Ensure matched cells
    common = expr_df.index.intersection(meta_df.index)
    expr_df = expr_df.loc[common]
    meta_df = meta_df.loc[common]

    # Identify sample and control groups
    ad_cells = meta_df[meta_df['oupSample.batchCond'] == 'AD'].index
    ct_cells = meta_df[meta_df['oupSample.batchCond'] == 'CT'].index

    # Analyse each gene: AD vs CT
    results, pvals = [], []

    for gene in expr_df.columns:
        ad_vals = expr_df.loc[ad_cells, gene]
        ct_vals = expr_df.loc[ct_cells, gene]

        log2fc = np.log2(ad_vals.mean() + 1e-6) - np.log2(ct_vals.mean() + 1e-6)
        stat, pval = ttest_ind(ad_vals, ct_vals, equal_var=False)
        results.append((gene, log2fc, pval))
        pvals.append(pval)

    # FDR correction, for p-value => FDR < 0.05
    _, fdr_vals, _, _ = multipletests(pvals, method="fdr_bh")

    deg_df = pd.DataFrame(results, columns=["gene", "logfoldchanges", "pval"])
    deg_df["FDR"] = fdr_vals
    deg_df = deg_df.sort_values(by="FDR") #sorting

    # Save results
    deg_df.to_csv(OUTPUT_DEG_CSV, index=False)
    print(f"Saved DEG to {OUTPUT_DEG_CSV} – {deg_df.shape[0]} genes")

    return deg_df


def plot_umap(expr_df: pd.DataFrame,
                      meta_df: pd.DataFrame,
                      group_col: str,
                      title: str = "UMAP",
                      output_path: str = RESULT_DIR / "umap_plot.png"):
    """
    Run UMAP using expression DataFrame and plot grouped by a specified metadata column.
    """
    # --- 1. Align index ---
    common_ids = expr_df.index.intersection(meta_df.index)
    expr_df = expr_df.loc[common_ids]
    meta_df = meta_df.loc[common_ids]

    #? --- 2. Standardise data ---
    scaled_data = StandardScaler().fit_transform(expr_df)

    #? --- 3. Reduce to 30 PC dimensions (faster UMAP) ---
    pca_data = PCA(n_components=30).fit_transform(scaled_data)

    # --- 4. UMAP ---
    reducer = umap.UMAP(n_components=2, random_state=42)
    embedding = reducer.fit_transform(pca_data)

    # --- 5. Prepare DataFrame for plotting ---
    plot_df = meta_df.copy()
    plot_df["UMAP1"] = embedding[:, 0]
    plot_df["UMAP2"] = embedding[:, 1]

    # --- 6. Plot using Seaborn ---
    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=plot_df, x="UMAP1", y="UMAP2",
                    hue=group_col, palette="Set1", s=50, edgecolor="k")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved: {output_path}")



def plot_volcano(deg_df, output_path= RESULT_DIR / "volcano_plot_AD.png"):
    # addcol -log10(FDR)
    deg_df["-log10(FDR)"] = -np.log10(deg_df["pvals_adj"] + 1e-10)

    # Topgenes
    deg_df["significant"] = (deg_df["pvals_adj"] < 0.05) & (abs(deg_df["logfoldchanges"]) > 1)

    # 畫 Volcano Plot
    plt.figure(figsize=(8, 6))
    sns.scatterplot(
        data=deg_df,
        x="logfoldchanges",
        y="-log10(FDR)",
        hue="significant",
        palette={True: "red", False: "grey"},
        legend=False
    )
    plt.title("Volcano Plot: AD vs CT")
    plt.xlabel("log2 Fold Change")
    plt.ylabel("-log10(FDR)")
    plt.tight_layout()
    plt.savefig(output_path, dpi=600)
    plt.close()
    print(f"✅ Volcano plot saved to: {output_path}")

def run_go_bp_enrichment(genes, label, result_dir: Path,
                         gene_sets="GO_Biological_Process_2021",
                         organism="Human", cutoff=0.05, top_terms=20):

    subdir = result_dir / f"enrichr_go_{label}_bp"
    subdir.mkdir(parents=True, exist_ok=True)

    # 1. Enrichment
    enr = enrichr(
        gene_list=genes,
        gene_sets=gene_sets,
        organism=organism,
        outdir=str(subdir),
        cutoff=cutoff
    )

    # 2. Dotplot of top terms
    out_png = subdir / f"go_bp_{label.lower()}_dotplot.png"
    dotplot(
        enr.results,
        title=f"GO Biological Process – {label}",
        top_term=top_terms,
        ofname=str(out_png)
    )
    print(f"▶ GO BP {label} dotplot saved to {out_png}")



#? Main function
def main():
    # I. Data loading and preprocessing
    #i. load expression profile table: gene vs samples
    expr_df = load_expression_data(EXPR_FILE)
    print(expr_df.head())
    print(expr_df.describe())
    
    #ii. load sample metadata: samples vs condition
    meta_df = load_metadata(META_FILE)
    print(meta_df.head())

    #iii. Prepreocessing
    #filtered and normalised + log1p
    expr_df, meta_df, adata, adata.obs = scanpy_preprocess(expr_df, meta_df)
    print(expr_df.head())
    print(expr_df.describe())
    print(meta_df.head())

    #iv. exploratory PCA: group by conditions 


    sc.pp.neighbors(adata, n_neighbors=10, n_pcs=30)  # builds the neighbour graph
    sc.tl.umap(adata)  # Running UMAP, computes the UMAP and stores in .obsm["X_umap"]
    sc.tl.leiden(adata, resolution=0.5, flavor="igraph", directed=False, n_iterations=2)

    sc.pl.umap(
    adata,
    color=["oupSample.batchCond", "oupSample.cellType_batchCond"],
    ncols=2,
    title=["AD vs CT", "AD vs CT - Cell Types"],
    # save="UMAP_plot_explorative.png"
    show=False
    )
    # Save manually with tight bounding box
    plt.savefig(RESULT_DIR / "UMAP_plot_explorative.png", dpi=600, bbox_inches="tight")
    plt.close()


    #iv. DEG
    
    sc.tl.rank_genes_groups(
        adata,
        groupby="oupSample.batchCond",  # 
        method="wilcoxon",                # "wilcoxon"
        use_raw=False,
        n_genes=1000 #show most DE 1000 genes
    )
    deg_df = sc.get.rank_genes_groups_df(adata, group="AD")  # AD ->VS CT
    deg_df.to_csv(RESULT_DIR / "scanpy_deg_AD.csv", index=False) 

    #pick top 20 genes
    # 揀 top 20 upregulated + 20 downregulated
    deg_df_sorted = deg_df.sort_values(by="logfoldchanges", ascending=False)
    top20_up = deg_df_sorted.head(20) #Pos: UP
    top20_down = deg_df_sorted.tail(20) #Neg: DOWN
    top_genes = pd.concat([top20_up, top20_down])["names"].tolist()

    #plot Heatmap for top 20 genes: Cell tyeps vs Genes
    sc.pl.heatmap(
        adata,
        var_names=top_genes,
        groupby="oupSample.cellType",
        cmap="bwr",
        standard_scale="var",  # normalise each gene: z-score
        swap_axes=True,
        show=False,
        dendrogram=True
        # save="../results/heatmap_ADvsCT.png"
    )

    # Save manually with tight bounding box
    plt.savefig(RESULT_DIR / "heatmap_ADvsCT.png", dpi=600, bbox_inches="tight")
    plt.close()

    #Volcano plots
    plot_volcano(deg_df)

    #v. Pathway Enrichment Analysis
    up_genes = top20_up["names"].tolist()
    down_genes = top20_down["names"].tolist()

    # # GO
    # # Example: GO Biological Process enrichment
    # (RESULT_DIR / "enrichr_go_UP_bp").mkdir(parents=True, exist_ok=True)
    # enr = enrichr(
    #     gene_list=up_genes,
    #     gene_sets="GO_Biological_Process_2021",
    #     organism="Human",
    #     outdir=str(RESULT_DIR / "enrichr_go_UP_bp"),
    #     cutoff=0.05
    # )

    # # Dot plot of top 20 terms
    # dotplot(enr.results, 
    #     title="GO Biological Process – UP", 
    #     top_term=20,
    #     ofname= str(RESULT_DIR / "/go_bp_up_dotplot.png"))

    # (RESULT_DIR / "enrichr_go_DOWN_bp").mkdir(parents=True, exist_ok=True)
    # enr = enrichr(
    #     gene_list=down_genes,
    #     gene_sets="GO_Biological_Process_2021",
    #     organism="Human",
    #     outdir=str(RESULT_DIR / "enrichr_go_DOWN_bp"),
    #     cutoff=0.05
    # )

    # # Dot plot of top 20 terms
    # dotplot(enr.results, 
    #     title="GO Biological Process – DOWN", 
    #     top_term=20,
    #     ofname=str(RESULT_DIR / "enrichr_go_DOWN_bp/go_bp_down_dotplot.png"))


    # #flag file - completion #!
    # flag_file = RESULT_DIR / 'completed.flag'
    # flag_file.write_text('done')


#! Main execution
if __name__ == "__main__":
    main()
