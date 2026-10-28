import { Center, Loader } from '@mantine/core';
import { Navigate, Outlet } from 'react-router-dom';

import type { Role } from '../api/types';
import { homeFor, useAuth } from './AuthContext';

export function RequireRole({ roles }: { roles: Role[] }) {
  const { user, isLoading } = useAuth();
  if (isLoading) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.includes(user.role)) return <Navigate to={homeFor(user.role)} replace />;
  return <Outlet />;
}
