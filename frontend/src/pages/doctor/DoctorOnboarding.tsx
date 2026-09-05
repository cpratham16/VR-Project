import { useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../../api/client';
import { useAuth } from '../../contexts/AuthContext';
import { Card, CardContent, Button, Badge, Container, SectionHeading } from '../../components/ui';

const MAX_MB = 5;
const ACCEPTED = ['application/pdf', 'image/jpeg', 'image/png'];

export default function DoctorOnboarding() {
  const [file, setFile] = useState<File | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { user, login } = useAuth();

  const reviewStatus = user?.role === 'doctor' ? user.review_status ?? 'pending' : 'approved';
  const hasCredentials = !!user?.has_credentials;

  const pickFile = (f: File | null | undefined) => {
    setError('');
    if (!f) return;
    if (!ACCEPTED.includes(f.type)) {
      setError('Only PDF, JPEG, or PNG files are accepted.');
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      setError(`File exceeds the ${MAX_MB} MB limit.`);
      return;
    }
    setFile(f);
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please attach your credential document first.');
      return;
    }
    setUploading(true);
    setError('');
    try {
      const data = new FormData();
      data.append('file', file);
      await apiClient.post('/doctor/profile/credential', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      await refreshUser();
      navigate('/doctor/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
      setUploading(false);
    }
  };

  const refreshUser = async () => {
    try {
      const meRes = await apiClient.get('/auth/me');
      const token = localStorage.getItem('token');
      if (token && meRes.data) login(token, meRes.data);
    } catch {
      /* keep existing state */
    }
  };

  return (
    <Container size="sm" className="py-14">
      <div className="motion-safe:animate-fade-in-up">
        <SectionHeading
          align="center"
          eyebrow="Credential verification"
          title={
            reviewStatus === 'rejected'
              ? 'Your document was not accepted'
              : reviewStatus === 'pending' && hasCredentials
                ? 'Your credentials are under review'
                : 'Verify your credentials'
          }
          description={
            reviewStatus === 'rejected'
              ? 'An administrator reviewed your submission and it was declined. You can upload a corrected document to restart the review.'
              : reviewStatus === 'pending' && hasCredentials
                ? 'We have your document. Our admin team is reviewing it — this usually takes one business day. You will get full access as soon as it is approved.'
                : 'Upload your medical council license or registration document. Our admin team reviews it before your profile becomes visible to patients.'
          }
          className="mb-10"
        />

        <Card variant="elevated" className="p-6 sm:p-8">
          <CardContent className="space-y-6 p-0">
            <div className="grid grid-cols-1 gap-3 rounded-lg bg-slate-50 p-4 text-sm sm:grid-cols-2">
              <InfoRow label="Name" value={user?.full_name || '—'} />
              <InfoRow label="Email" value={user?.email} />
            </div>

            {reviewStatus === 'pending' && hasCredentials ? (
              <div className="space-y-4">
                <div className="flex flex-col items-center gap-3 rounded-lg border border-teal-100 bg-muted/70 p-8 text-center">
                  <span aria-hidden="true" className="text-3xl motion-safe:animate-pulse-soft">⏳</span>
                  <Badge variant="primary" dot>Under review</Badge>
                  <p className="max-w-sm text-xs leading-relaxed text-slate-600">
                    While you wait you can sign out or explore the landing page. Patients cannot see your profile and
                    appointment requests stay locked until an administrator approves your credentials.
                  </p>
                </div>
                <Button variant="outline" onClick={() => window.location.reload()} className="w-full">
                  Refresh status
                </Button>
              </div>
            ) : (
              <>
                {reviewStatus === 'rejected' && user?.rejection_reason && (
                  <div role="alert" className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-relaxed text-rose-700">
                    <strong>Admin feedback:</strong> {user.rejection_reason}
                  </div>
                )}
                <div
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragOver(true);
                  }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={(e) => {
                    e.preventDefault();
                    setDragOver(false);
                    pickFile(e.dataTransfer.files?.[0]);
                  }}
                  onClick={() => inputRef.current?.click()}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
                  aria-label="Upload credential document"
                  className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-10 text-center transition-all duration-200 ${
                    dragOver
                      ? 'border-teal-500 bg-muted/70 ring-4 ring-teal-500/10'
                      : 'border-slate-300 hover:border-teal-400 hover:bg-slate-50'
                  }`}
                >
                  <span aria-hidden="true" className="text-3xl">📄</span>
                  {file ? (
                    <>
                      <p className="text-sm font-semibold text-slate-900">{file.name}</p>
                      <Badge variant="success" size="sm">
                        {(file.size / 1024 / 1024).toFixed(2)} MB · ready to upload
                      </Badge>
                    </>
                  ) : (
                    <>
                      <p className="text-sm font-semibold text-slate-700">
                        Drag &amp; drop your document here, or <span className="text-accent">browse</span>
                      </p>
                      <p className="text-xs text-slate-400">PDF, JPEG, or PNG · up to {MAX_MB} MB</p>
                    </>
                  )}
                  <input
                    ref={inputRef}
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    className="hidden"
                    onChange={(e) => pickFile(e.target.files?.[0])}
                  />
                </div>

                {error && (
                  <p role="alert" className="rounded-md border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">
                    {error}
                  </p>
                )}

                <Button onClick={handleUpload} isLoading={uploading} size="lg" className="w-full">
                  {reviewStatus === 'rejected' ? 'Re-submit for verification' : 'Submit for verification'}
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </Container>
  );
}

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  return (
    <div>
      <dt className="text-[11px] font-bold uppercase tracking-[0.08em] text-slate-500">{label}</dt>
      <dd className="mt-0.5 font-medium text-slate-900">{value}</dd>
    </div>
  );
}
