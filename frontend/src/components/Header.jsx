import React from 'react';

function Header() {
  return (
    <header className="app-header">
      <div className="logo">
        <span className="logo-icon">📈</span>
        <span className="logo-text">Trending News</span>
      </div>
      <div className="header-tagline">Discover what's happening right now</div>
    </header>
  );
}

export default Header;
