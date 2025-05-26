import React, { useEffect, useState } from 'react';

// Define the BeforeInstallPromptEvent interface
interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

const InstallPrompt: React.FC = () => {
  const [installPromptEvent, setInstallPromptEvent] = useState<BeforeInstallPromptEvent | null>(null);
  const [showPrompt, setShowPrompt] = useState<boolean>(false);

  useEffect(() => {
    const handleBeforeInstallPrompt = (e: Event) => {
      // Prevent Chrome 67 and earlier from automatically showing the prompt
      e.preventDefault();
      // Stash the event so it can be triggered later
      setInstallPromptEvent(e as BeforeInstallPromptEvent);
      // Check if the user has already dismissed or installed
      const hasPrompted = localStorage.getItem('installPromptDismissed');
      if (!hasPrompted) {
        setShowPrompt(true);
      }
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);

  const handleInstallClick = () => {
    if (!installPromptEvent) return;

    // Show the install prompt
    installPromptEvent.prompt();

    // Wait for the user to respond to the prompt
    installPromptEvent.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('User accepted the install prompt');
      } else {
        console.log('User dismissed the install prompt');
      }
      // Clear the saved prompt since it can't be used again
      setInstallPromptEvent(null);
      setShowPrompt(false);
    });
  };

  const handleDismiss = () => {
    // Remember that the user has dismissed the prompt
    localStorage.setItem('installPromptDismissed', 'true');
    setShowPrompt(false);
  };

  if (!showPrompt) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 p-4 z-50" style={{ backgroundColor: 'var(--bs-primary)', color: 'white' }}>
      <div className="container mx-auto flex justify-between items-center">
        <div>
          <p className="font-medium">Install Sensylate</p>
          <p className="text-sm opacity-90">Add to your home screen for quick access</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleDismiss}
            className="px-3 py-1 rounded"
            style={{
              color: 'white',
              backgroundColor: 'transparent',
              border: '1px solid white'
            }}
          >
            Not now
          </button>
          <button
            onClick={handleInstallClick}
            className="px-3 py-1 rounded"
            style={{
              color: 'var(--bs-primary)',
              backgroundColor: 'white',
              border: '1px solid white'
            }}
          >
            Install
          </button>
        </div>
      </div>
    </div>
  );
};

export default InstallPrompt;