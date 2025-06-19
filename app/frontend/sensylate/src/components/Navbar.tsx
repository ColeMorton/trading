import React, { useState } from 'react';
import Icon from './Icon';
import { icons } from '../utils/icons';
import { useAppContext } from '../context/AppContext';

const Navbar: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { currentView, setCurrentView } = useAppContext();

  const toggleNavbar = () => {
    setIsOpen(!isOpen);
  };

  const handleNavClick = (
    view: 'csv-viewer' | 'parameter-testing' | 'position-sizing'
  ) => {
    setCurrentView(view);
    setIsOpen(false); // Close mobile menu
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
        <div
          className={`collapse navbar-collapse ${isOpen ? 'show' : ''}`}
          id="navbarNav"
        >
          <ul className="navbar-nav">
            <li className="nav-item">
              <button
                className={`nav-link btn btn-link ${
                  currentView === 'csv-viewer' ? 'active' : ''
                }`}
                aria-current={currentView === 'csv-viewer' ? 'page' : undefined}
                onClick={() => handleNavClick('csv-viewer')}
              >
                <Icon icon={icons.file} className="me-2" />
                CSV Viewer
              </button>
            </li>
            <li className="nav-item">
              <button
                className={`nav-link btn btn-link ${
                  currentView === 'parameter-testing' ? 'active' : ''
                }`}
                aria-current={
                  currentView === 'parameter-testing' ? 'page' : undefined
                }
                onClick={() => handleNavClick('parameter-testing')}
                data-testid="nav-parameter-testing"
              >
                <Icon icon={icons.parameterTesting} className="me-2" />
                Parameter Testing
              </button>
            </li>
            <li className="nav-item">
              <button
                className={`nav-link btn btn-link ${
                  currentView === 'position-sizing' ? 'active' : ''
                }`}
                aria-current={
                  currentView === 'position-sizing' ? 'page' : undefined
                }
                onClick={() => handleNavClick('position-sizing')}
                data-testid="nav-position-sizing"
              >
                <Icon icon={icons.calculator} className="me-2" />
                Position Sizing
              </button>
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
