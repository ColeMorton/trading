import React from 'react';
import Icon from './Icon';
import { icons } from '../utils/icons';

const Footer: React.FC = () => {
  return (
    <footer className="footer mt-auto py-3 bg-dark">
      <div className="container text-center">
        <span className="text-muted">
          <Icon icon={icons.copyright} className="me-1" />
          Sensylate 2025 - Sensitivity Analysis meets Strategy Portfolio Management
        </span>
      </div>
    </footer>
  );
};

export default Footer;