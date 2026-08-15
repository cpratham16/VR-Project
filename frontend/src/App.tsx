import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, useState, type ReactNode } from 'react';
import MainLayout from './layouts/MainLayout';
import Home from './pages/Home';
import Login from './pages/auth/Login';
import Signup from './pages/auth/Signup';
import PatientDashboard from './pages/patient/Dashboard';
import ConsentScreen from './pages/patient/onboarding/ConsentScreen';
import ProfileSetup from './pages/patient/onboarding/ProfileSetup';
import ScreeningPage from './pages/patient/screening/ScreeningPage';
import MoodTrackerPage from './pages/patient/mood/MoodTrackerPage';
import AIChatPage from './pages/patient/chat/AIChatPage';
import CommunityPage from './pages/patient/community/CommunityPage';
import VRTherapyPage from './pages/patient/vr/VRTherapyPage';
import DoctorTriageDashboard from './pages/doctor/TriageDashboard';
import ModerationQueuePage from './pages/doctor/ModerationQueuePage';
import VRAssignmentPage from './pages/doctor/VRAssignmentPage';
import DoctorPatientDetail from './pages/doctor/PatientDetail';
import PatientAppointmentsPage from './pages/patient/AppointmentsPage';
import DoctorAppointmentsPage from './pages/doctor/DoctorAppointments';
import AdminDashboard from './pages/admin/AdminDashboard';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { apiClient } from './api/client';

function ProtectedRoute({ children, allowedRoles }: { children: ReactNode, allowedRoles?: string[] }) {
  const { user, isLoading } = useAuth();
  
  if (isLoading) return <div className="p-10 text-center">Loading...</div>;
  if (!user) return <Navigate to="/auth/login" replace />;
  if (allowedRoles && !allowedRoles.includes(user.role)) return <Navigate to="/" replace />;
  
  return children as React.ReactElement;
}

function RequireOnboarding({ children }: { children: ReactNode }) {
  const [onboardingState, setOnboardingState] = useState<'loading' | 'needs_consent' | 'needs_profile' | 'ready'>('loading');

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await apiClient.get('/patient/status');
        if (!res.data.has_consent) {
          setOnboardingState('needs_consent');
        } else if (!res.data.has_profile) {
          setOnboardingState('needs_profile');
        } else {
          setOnboardingState('ready');
        }
      } catch (e) {
        setOnboardingState('needs_consent');
      }
    };
    checkStatus();
  }, []);

  if (onboardingState === 'loading') return <div className="p-10 text-center">Checking onboarding status...</div>;
  if (onboardingState === 'needs_consent') return <Navigate to="/patient/onboarding/consent" replace />;
  if (onboardingState === 'needs_profile') return <Navigate to="/patient/onboarding/profile" replace />;
  
  return children as React.ReactElement;
}

function AppContent() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Home />} />
        
        {/* Auth routes */}
        <Route path="auth/login" element={<Login />} />
        <Route path="auth/signup" element={<Signup />} />
        
        {/* Patient Panel */}
        <Route path="patient">
          {/* Un-guarded section for onboarding */}
          <Route path="onboarding/consent" element={
            <ProtectedRoute allowedRoles={['patient']}>
              <ConsentScreen />
            </ProtectedRoute>
          } />
          <Route path="onboarding/profile" element={
            <ProtectedRoute allowedRoles={['patient']}>
              <ProfileSetup />
            </ProtectedRoute>
          } />
          
          {/* Guarded Patient Section */}
          <Route path="dashboard" element={
            <ProtectedRoute allowedRoles={['patient']}>
              <RequireOnboarding>
                <PatientDashboard />
              </RequireOnboarding>
            </ProtectedRoute>
          } />
          <Route path="screening" element={
            <ProtectedRoute allowedRoles={['patient']}>
              <RequireOnboarding>
                <ScreeningPage />
              </RequireOnboarding>
            </ProtectedRoute>
          } />
          <Route path="mood" element={
            <ProtectedRoute allowedRoles={['patient']}>
              <RequireOnboarding>
                <MoodTrackerPage />
              </RequireOnboarding>
            </ProtectedRoute>
          } />
          <Route path="chat" element={
            <ProtectedRoute allowedRoles={['patient']}>
              <RequireOnboarding>
                <AIChatPage />
              </RequireOnboarding>
            </ProtectedRoute>
          } />
          <Route path="community" element={
            <ProtectedRoute allowedRoles={['patient']}>
              <RequireOnboarding>
                <CommunityPage />
              </RequireOnboarding>
            </ProtectedRoute>
          } />
          <Route path="appointments" element={
            <ProtectedRoute allowedRoles={['patient']}>
              <RequireOnboarding>
                <PatientAppointmentsPage />
              </RequireOnboarding>
            </ProtectedRoute>
          } />
          <Route path="vr" element={
            <ProtectedRoute allowedRoles={['patient']}>
              <RequireOnboarding>
                <VRTherapyPage />
              </RequireOnboarding>
            </ProtectedRoute>
          } />
        </Route>
        
        {/* Doctor Panel */}
        <Route path="doctor">
          <Route path="dashboard" element={
            <ProtectedRoute allowedRoles={['doctor', 'admin']}>
              <DoctorTriageDashboard />
            </ProtectedRoute>
          } />
          <Route path="moderation" element={
            <ProtectedRoute allowedRoles={['doctor', 'admin']}>
              <ModerationQueuePage />
            </ProtectedRoute>
          } />
          <Route path="vr" element={
            <ProtectedRoute allowedRoles={['doctor', 'admin']}>
              <VRAssignmentPage />
            </ProtectedRoute>
          } />
          <Route path="patient/:patientId" element={
            <ProtectedRoute allowedRoles={['doctor', 'admin']}>
              <DoctorPatientDetail />
            </ProtectedRoute>
          } />
          <Route path="appointments" element={
            <ProtectedRoute allowedRoles={['doctor', 'admin']}>
              <DoctorAppointmentsPage />
            </ProtectedRoute>
          } />
        </Route>
        
        {/* Admin Panel */}
        <Route path="admin">
          <Route path="dashboard" element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          } />
        </Route>
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppContent />
      </BrowserRouter>
    </AuthProvider>
  );
}
