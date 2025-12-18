'use client';

import { createContext, useContext, useState, useCallback } from 'react';
import Toast from '@/app/components/Toast';
import Modal from '@/app/components/Modal';

interface ToastOptions {
  message: string;
  type?: 'success' | 'error' | 'info';
  duration?: number;
}

interface ModalOptions {
  title: string;
  message: string;
  type?: 'confirm' | 'alert';
  confirmText?: string;
  cancelText?: string;
}

interface NotificationContextType {
  showToast: (options: ToastOptions) => void;
  showModal: (options: ModalOptions) => Promise<boolean>;
}

const NotificationContext = createContext<NotificationContextType | null>(null);

export function NotificationProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [toast, setToast] = useState<ToastOptions | null>(null);
  const [modal, setModal] = useState<
    (ModalOptions & { resolve: (value: boolean) => void }) | null
  >(null);

  const showToast = useCallback((options: ToastOptions) => {
    setToast(options);
  }, []);

  const showModal = useCallback((options: ModalOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      setModal({ ...options, resolve });
    });
  }, []);

  const handleModalConfirm = () => {
    if (modal) {
      modal.resolve(true);
      setModal(null);
    }
  };

  const handleModalCancel = () => {
    if (modal) {
      modal.resolve(false);
      setModal(null);
    }
  };

  return (
    <NotificationContext.Provider value={{ showToast, showModal }}>
      {children}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          duration={toast.duration}
          onClose={() => setToast(null)}
        />
      )}
      {modal && (
        <Modal
          title={modal.title}
          message={modal.message}
          type={modal.type}
          confirmText={modal.confirmText}
          cancelText={modal.cancelText}
          onConfirm={handleModalConfirm}
          onCancel={modal.type === 'confirm' ? handleModalCancel : undefined}
        />
      )}
    </NotificationContext.Provider>
  );
}

export function useNotification() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within NotificationProvider');
  }
  return context;
}
