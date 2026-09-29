import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { Card, CardContent, Button, Input } from '@/components/ui';
import { Mail, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

export function AuthPage() {
  const { login, completeLogin, isAuthenticated, isLoading } = useAuth();
  const [step, setStep] = useState<'start' | 'device_code' | 'waiting' | 'success' | 'error'>('start');
  const [deviceCode, setDeviceCode] = useState('');
  const [userCode, setUserCode] = useState('');
  const [verificationUri, setVerificationUri] = useState('');
  const [message, setMessage] = useState('');
  const [expiresIn, setExpiresIn] = useState(0);
  const [interval, setInterval] = useState(0);
  const [error, setError] = useState('');
  const [polling, setPolling] = useState(false);
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    if (isAuthenticated) {
      setStep('success');
    }
  }, [isAuthenticated]);

  const handleStartLogin = async () => {
    setError('');
    try {
      const response = await login();
      setDeviceCode(response.device_code);
      setUserCode(response.user_code);
      setVerificationUri(response.verification_uri);
      setMessage(response.message);
      setExpiresIn(response.expires_in);
      setInterval(response.interval);
      setCountdown(response.expires_in);
      setStep('device_code');
      startPolling();
    } catch (err) {
      setError('Error al iniciar sesión. Inténtalo de nuevo.');
      setStep('error');
    }
  };

  const startPolling = () => {
    setPolling(true);
    const poll = async () => {
      while (polling && countdown > 0) {
        await new Promise(resolve => setTimeout(resolve, interval * 1000));
        setCountdown(prev => prev - interval);
        
        try {
          const response = await completeLogin(deviceCode);
          if (response.access_token) {
            setPolling(false);
            setStep('success');
            return;
          }
        } catch (err) {
          // Continue polling
        }
      }
      if (polling) {
        setPolling(false);
        setError('El código ha expirado. Inténtalo de nuevo.');
        setStep('error');
      }
    };
    poll();
  };

  const copyUserCode = () => {
    navigator.clipboard.writeText(userCode);
  };

  if (step === 'success') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-4">
        <Card className="w-full max-w-md">
          <CardContent className="py-10 text-center">
            <div className="p-3 rounded-full bg-green-100 dark:bg-green-900/30 inline-flex mb-4">
              <CheckCircle className="h-8 w-8 text-green-600 dark:text-green-400" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-2">¡Bienvenido!</h1>
            <p className="text-slate-500 dark:text-slate-400">Has iniciado sesión correctamente. Redirigiendo...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 p-4">
      <Card className="w-full max-w-md">
        <CardContent className="py-8">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">AI Workmate</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">Conecta tu cuenta de Microsoft para comenzar</p>
          </div>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 flex items-center gap-2 text-red-700 dark:text-red-400 text-sm">
              <AlertCircle className="h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {step === 'start' && (
            <Button className="w-full" size="lg" onClick={handleStartLogin} loading={isLoading}>
              <Mail className="h-5 w-5" />
              Conectar Microsoft Outlook
            </Button>
          )}

          {step === 'device_code' && (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700">
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                  1. Ve a <a href={verificationUri} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">{verificationUri}</a>
                </p>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                  2. Ingresa el código:
                </p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-2xl font-mono font-bold text-slate-900 dark:text-slate-100 bg-white dark:bg-slate-700 px-4 py-2 rounded-lg text-center border border-slate-200 dark:border-slate-600">
                    {userCode.match(/.{1,4}/g)?.join(' ') || userCode}
                  </code>
                  <Button variant="secondary" onClick={copyUserCode} size="sm">
                    Copiar
                  </Button>
                </div>
              </div>
              <p className="text-sm text-slate-500 dark:text-slate-400 text-center">
                Tiempo restante: <span className="font-mono font-bold">{Math.floor(countdown / 60)}:{String(countdown % 60).padStart(2, '0')}</span>
              </p>
              <Button variant="secondary" className="w-full" onClick={() => { setPolling(false); setStep('start'); }}>
                Cancelar
              </Button>
            </div>
          )}

          {step === 'error' && (
            <div className="text-center">
              <p className="text-slate-500 dark:text-slate-400 mb-4">No se pudo completar la autenticación.</p>
              <Button onClick={() => setStep('start')}>Intentar de nuevo</Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}