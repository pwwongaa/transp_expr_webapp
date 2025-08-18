// client/src/ErrorBoundary.jsx
import React from 'react'
export default class ErrorBoundary extends React.Component {
  state = { err: null }
  static getDerivedStateFromError(err){ return { err } }
  componentDidCatch(e, info){ console.error('App crash:', e, info) }
  render(){ return this.state.err ? <pre style={{padding:12}}>{String(this.state.err)}</pre> : this.props.children }
}

