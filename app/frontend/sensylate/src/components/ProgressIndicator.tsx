import React from 'react';
import Icon from './Icon';
import { icons } from '../utils/icons';

interface ProgressStep {
  id: string;
  label: string;
  status: 'pending' | 'active' | 'completed' | 'error';
  description?: string;
}

interface ProgressIndicatorProps {
  steps: ProgressStep[];
  currentStep?: string;
  title?: string;
  showPercentage?: boolean;
  percentage?: number;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'horizontal' | 'vertical';
}

const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  steps,
  title,
  showPercentage = false,
  percentage,
  className = '',
  size = 'md',
  variant = 'horizontal',
}) => {
  const completedSteps = steps.filter(
    (step) => step.status === 'completed'
  ).length;
  const totalSteps = steps.length;
  const progressPercentage =
    percentage ?? (totalSteps > 0 ? (completedSteps / totalSteps) * 100 : 0);

  const getStepIcon = (step: ProgressStep) => {
    switch (step.status) {
      case 'completed':
        return icons.success;
      case 'error':
        return icons.warning;
      case 'active':
        return icons.loading;
      default:
        return icons.lastUpdated;
    }
  };

  const getStepClass = (step: ProgressStep) => {
    const baseClass = 'step';
    switch (step.status) {
      case 'completed':
        return `${baseClass} step-completed`;
      case 'error':
        return `${baseClass} step-error`;
      case 'active':
        return `${baseClass} step-active`;
      default:
        return `${baseClass} step-pending`;
    }
  };

  const getSizeClass = () => {
    switch (size) {
      case 'sm':
        return 'progress-sm';
      case 'lg':
        return 'progress-lg';
      default:
        return 'progress-md';
    }
  };

  if (variant === 'vertical') {
    return (
      <div
        className={`progress-indicator progress-vertical ${getSizeClass()} ${className}`}
      >
        {title && (
          <div className="progress-title mb-3">
            <h6 className="mb-1">{title}</h6>
            {showPercentage && (
              <div className="progress-percentage">
                {Math.round(progressPercentage)}% Complete
              </div>
            )}
          </div>
        )}

        <div className="steps-container">
          {steps.map((step, index) => (
            <div key={step.id} className={getStepClass(step)}>
              <div className="step-connector">
                {index < steps.length - 1 && (
                  <div
                    className={`connector ${
                      step.status === 'completed' ? 'completed' : ''
                    }`}
                  />
                )}
              </div>

              <div className="step-icon">
                <Icon
                  icon={getStepIcon(step)}
                  className={step.status === 'active' ? 'fa-spin' : ''}
                />
              </div>

              <div className="step-content">
                <div className="step-label">{step.label}</div>
                {step.description && (
                  <div className="step-description text-muted small">
                    {step.description}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`progress-indicator progress-horizontal ${getSizeClass()} ${className}`}
    >
      {title && (
        <div className="progress-title mb-3">
          <div className="d-flex justify-content-between align-items-center">
            <h6 className="mb-0">{title}</h6>
            {showPercentage && (
              <span className="progress-percentage">
                {Math.round(progressPercentage)}%
              </span>
            )}
          </div>
        </div>
      )}

      {/* Progress Bar */}
      <div
        className="progress mb-3"
        style={{
          height: size === 'lg' ? '8px' : size === 'sm' ? '4px' : '6px',
        }}
      >
        <div
          className="progress-bar"
          role="progressbar"
          style={{ width: `${progressPercentage}%` }}
          aria-valuenow={progressPercentage}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>

      {/* Steps */}
      <div className="steps-container d-flex justify-content-between">
        {steps.map((step) => (
          <div
            key={step.id}
            className={`step-horizontal ${getStepClass(step)}`}
          >
            <div className="step-icon-container">
              <div className="step-icon">
                <Icon
                  icon={getStepIcon(step)}
                  className={step.status === 'active' ? 'fa-spin' : ''}
                />
              </div>
            </div>
            <div className="step-content text-center">
              <div className="step-label small">{step.label}</div>
              {step.description && size !== 'sm' && (
                <div
                  className="step-description text-muted"
                  style={{ fontSize: '0.75rem' }}
                >
                  {step.description}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProgressIndicator;
