import '@fontsource-variable/golos-text';
import '@mantine/core/styles.css';
import '@mantine/dates/styles.css';
import '@mantine/notifications/styles.css';
import './global.css';
import './lib/dates';

import { MantineProvider } from '@mantine/core';
import { DatesProvider } from '@mantine/dates';
import { ModalsProvider } from '@mantine/modals';
import { Notifications } from '@mantine/notifications';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

import { App } from './App';
import { AuthProvider } from './auth/AuthContext';
import { theme } from './theme';

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } });

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <MantineProvider theme={theme}>
        <DatesProvider settings={{ locale: 'ru', firstDayOfWeek: 1 }}>
          <ModalsProvider>
            <Notifications position="bottom-right" />
            <BrowserRouter>
              <AuthProvider>
                <App />
              </AuthProvider>
            </BrowserRouter>
          </ModalsProvider>
        </DatesProvider>
      </MantineProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
