import React, { useState } from 'react';
import Icon from './Icon';
import { icons } from '../utils/icons';

const Navbar: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleNavbar = () => {
    setIsOpen(!isOpen);
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
      <div className="container-fluid">
        <a className="navbar-brand" href="/">
          <Icon icon={icons.brand} className="me-2" />
          Sensylate
        </a>
        <button 
          className="navbar-toggler" 
          type="button" 
          onClick={toggleNavbar}
          aria-controls="navbarNav"
          aria-expanded={isOpen}
          aria-label="Toggle navigation"
        >
          <Icon icon={isOpen ? icons.times : icons.menu} />
        </button>
        <div className={`collapse navbar-collapse ${isOpen ? 'show' : ''}`} id="navbarNav">
          <ul className="navbar-nav">
            <li className="nav-item">
              <a className="nav-link active" aria-current="page" href="/">
                <Icon icon={icons.file} className="me-2" />
                CSV Viewer
              </a>
            </li>
            <li className="nav-item">
              <a className="nav-link" href="#portfolio-section">
                <Icon icon={icons.portfolio} className="me-2" />
                Portfolio Analysis
              </a>
            </li>
          </ul>
          <ul className="navbar-nav ms-auto">
            <li className="nav-item">
              <a className="nav-link" href="#" title="Settings">
                <Icon icon={icons.settings} />
                <span className="visually-hidden">Settings</span>
              </a>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;