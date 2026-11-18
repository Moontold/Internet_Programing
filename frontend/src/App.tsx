import { Navigate, Route, Routes } from 'react-router-dom';

import { homeFor, useAuth } from './auth/AuthContext';
import { RequireRole } from './auth/RequireRole';
import { AppShell } from './components/AppShell';
import { SectionPlaceholder } from './components/SectionPlaceholder';
import { LoginPage } from './pages/common/LoginPage';
import { ProfilePage } from './pages/common/ProfilePage';
import { ParentCardPage } from './pages/tutor/ParentCardPage';
import { ParentsPage } from './pages/tutor/ParentsPage';
import { StudentCardPage } from './pages/tutor/StudentCardPage';
import { StudentsPage } from './pages/tutor/StudentsPage';

function Home() {
  const { user } = useAuth();
  return <Navigate to={user ? homeFor(user.role) : '/login'} replace />;
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireRole roles={['tutor', 'parent', 'student']} />}>
        <Route path="/" element={<Home />} />
        <Route path="/profile" element={<AppShell><ProfilePage /></AppShell>} />
      </Route>
      <Route element={<RequireRole roles={['tutor']} />}>
        <Route path="/schedule" element={<AppShell><SectionPlaceholder title="Расписание" /></AppShell>} />
        <Route path="/students" element={<AppShell><StudentsPage /></AppShell>} />
        <Route path="/students/:studentId" element={<AppShell><StudentCardPage /></AppShell>} />
        <Route path="/parents" element={<AppShell><ParentsPage /></AppShell>} />
        <Route path="/parents/:parentId" element={<AppShell><ParentCardPage /></AppShell>} />
      </Route>
      <Route element={<RequireRole roles={['parent']} />}>
        <Route path="/children" element={<AppShell><SectionPlaceholder title="Дети" /></AppShell>} />
      </Route>
      <Route element={<RequireRole roles={['student']} />}>
        <Route path="/my/schedule" element={<AppShell><SectionPlaceholder title="Расписание" /></AppShell>} />
        <Route path="/my/lessons" element={<AppShell><SectionPlaceholder title="Занятия" /></AppShell>} />
      </Route>
      <Route path="*" element={<Home />} />
    </Routes>
  );
}
