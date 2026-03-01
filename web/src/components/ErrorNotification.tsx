/**
 * エラー通知コンポーネント
 */

import React, { useEffect, useState } from 'react';

interface ErrorNotificationProps {
  message: string;
  onClose: () => void;
  duration?: number;
}

export const ErrorNotification: React.FC<ErrorNotificationProps> = ({
  message,
  onClose,
  duration = 5000,
}) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(onClose, 300); // フェードアウトアニメーション後にクローズ
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(onClose, 300);
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        backgroundColor: '#ef4444',
        color: 'white',
        padding: '16px 24px',
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        maxWidth: '400px',
        zIndex: 9999,
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'translateY(0)' : 'translateY(-10px)',
        transition: 'opacity 0.3s, transform 0.3s',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '12px',
      }}
    >
      <div style={{ flex: 1 }}>{message}</div>
      <button
        onClick={handleClose}
        style={{
          background: 'transparent',
          border: 'none',
          color: 'white',
          cursor: 'pointer',
          fontSize: '20px',
          lineHeight: '1',
          padding: '0',
        }}
      >
        ×
      </button>
    </div>
  );
};

// エラー通知管理用のコンテキスト
interface ErrorContextValue {
  showError: (message: string) => void;
}

const ErrorContext = React.createContext<ErrorContextValue | null>(null);

export const ErrorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [errors, setErrors] = useState<Array<{ id: number; message: string }>>([]);
  const [nextId, setNextId] = useState(0);

  const showError = (message: string) => {
    const id = nextId;
    setNextId((prev) => prev + 1);
    setErrors((prev) => [...prev, { id, message }]);
  };

  const removeError = (id: number) => {
    setErrors((prev) => prev.filter((error) => error.id !== id));
  };

  return (
    <ErrorContext.Provider value={{ showError }}>
      {children}
      {errors.map((error) => (
        <ErrorNotification
          key={error.id}
          message={error.message}
          onClose={() => removeError(error.id)}
        />
      ))}
    </ErrorContext.Provider>
  );
};

export const useError = () => {
  const context = React.useContext(ErrorContext);
  if (!context) {
    throw new Error('useError must be used within ErrorProvider');
  }
  return context;
};
