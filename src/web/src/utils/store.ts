/**
 * Global state management using Zustand
 */

import { create } from 'zustand';
import { Settings, ScanProgress } from '../api/client';

interface AppState {
  // Theme
  darkMode: boolean;
  toggleDarkMode: () => void;

  // Settings
  settings: Settings | null;
  setSettings: (settings: Settings) => void;

  // Current scan
  currentScan: ScanProgress | null;
  setCurrentScan: (scan: ScanProgress | null) => void;

  // Notifications
  notifications: Array<{ id: string; type: 'success' | 'error' | 'info' | 'warning'; message: string }>;
  addNotification: (type: 'success' | 'error' | 'info' | 'warning', message: string) => void;
  removeNotification: (id: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Theme
  darkMode: localStorage.getItem('darkMode') === 'true',
  toggleDarkMode: () =>
    set((state) => {
      const newMode = !state.darkMode;
      localStorage.setItem('darkMode', String(newMode));
      return { darkMode: newMode };
    }),

  // Settings
  settings: null,
  setSettings: (settings) => set({ settings }),

  // Current scan
  currentScan: null,
  setCurrentScan: (scan) => set({ currentScan: scan }),

  // Notifications
  notifications: [],
  addNotification: (type, message) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        { id: Date.now().toString(), type, message },
      ],
    })),
  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),
}));
