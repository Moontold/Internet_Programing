import { Navigate, Route, Routes } from 'react-router-dom';

import { homeFor, useAuth } from './auth/AuthContext';
import { RequireRole } from './auth/RequireRole';
import { AppShell } from './components/AppShell';
import { LessonPage } from './pages/common/LessonPage';
import { LoginPage } from './pages/common/LoginPage';
import { ProfilePage } from './pages/common/ProfilePage';
import { ChildLessonsPage } from './pages/parent/ChildLessonsPage';
import { ChildrenPage } from './pages/parent/ChildrenPage';
import { StudentLessonsPage } from './pages/student/StudentLessonsPage';
import { StudentSchedulePage } from './pages/student/StudentSchedulePage';
import { ParentCardPage } from './pages/tutor/ParentCardPage';
import { ParentsPage } from './pages/tutor/ParentsPage';
import { SchedulePage } from './pages/tutor/SchedulePage';
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
        <Route path="/lessons/:lessonId" element={<AppShell><LessonPage /></AppShell>} />
      </Route>
      <Route element={<RequireRole roles={['tutor']} />}>
        <Route path="/schedule" element={<AppShell><SchedulePage /></AppShell>} />
        <Route path="/students" element={<AppShell><StudentsPage /></AppShell>} />
        <Route path="/students/:studentId" element={<AppShell><StudentCardPage /></AppShell>} />
        <Route path="/parents" element={<AppShell><ParentsPage /></AppShell>} />
        <Route path="/parents/:parentId" element={<AppShell><ParentCardPage /></AppShell>} />
      </Route>
      <Route element={<RequireRole roles={['parent']} />}>
        <Route path="/children" element={<AppShell><ChildrenPage /></AppShell>} />
        <Route path="/children/:studentId/lessons" element={<AppShell><ChildLessonsPage /></AppShell>} />
      </Route>
      <Route element={<RequireRole roles={['student']} />}>
        <Route path="/my/schedule" element={<AppShell><StudentSchedulePage /></AppShell>} />
        <Route path="/my/lessons" element={<AppShell><StudentLessonsPage /></AppShell>} />
      </Route>
      <Route path="*" element={<Home />} />
    </Routes>
  );
}
