import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { apiClient } from '../../api/client';
import { Card, CardContent, Button, Input } from '../../components/ui';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      const formData = new URLSearchParams();
      formData.append('username', email); // OAuth2 expects 'username' instead of 'email'
      formData.append('password', password);

      const res = await apiClient.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      const token = res.data.access_token;

      // Fetch user profile
      const userRes = await apiClient.get('/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      });

      login(token, userRes.data);

      // Redirect based on role
      if (userRes.data.role === 'patient') navigate('/patient/dashboard');
      else if (userRes.data.role === 'doctor') navigate('/doctor/dashboard');
      else navigate('/admin/dashboard');

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-md px-4 py-16">
      <div className="mb-8 flex flex-col items-center gap-3 text-center">
        <span className="small-caps text-accent">Welcome back</span>
        <h1 className="font-display text-4xl font-medium tracking-normal text-foreground">
          Log in to Mindora
        </h1>
        <div aria-hidden="true" className="flex w-full max-w-[120px] items-center gap-3 pt-1">
          <span className="h-px flex-1 bg-[#e8e4df]" />
          <span className="h-1 w-1 rotate-45 bg-accent" />
          <span className="h-px flex-1 bg-[#e8e4df]" />
        </div>
      </div>

      <Card variant="elevated">
        <CardContent className="p-8">
          <form onSubmit={handleSubmit} className="space-y-5" noValidate={false}>
            {error && (
              <div role="alert" className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                {error}
              </div>
            )}

            <Input
              label="Email address"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <Input
              label="Password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <Button type="submit" isLoading={submitting} className="w-full">
              Sign in
            </Button>
          </form>
        </CardContent>
      </Card>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        New to Mindora?{' '}
        <Link
          to="/auth/signup"
          className="font-medium text-accent underline decoration-accent/40 underline-offset-4 transition-colors hover:decoration-accent"
        >
          Create an account
        </Link>
      </p>
    </div>
  );
}
