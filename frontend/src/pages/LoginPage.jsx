import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { GraduationCap, ArrowRight, Loader2 } from 'lucide-react';
import useStore from '../store/useStore';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, authLoading, authError } = useStore();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = await login(email, password);
      navigate(data.is_onboarded ? '/' : '/onboarding');
    } catch {}
  };

  return (
    <div className="min-h-screen flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-surface-950 text-white flex-col justify-between p-12">
        <div>
          <div className="flex items-center gap-3 mb-16">
            <GraduationCap className="w-9 h-9 text-brand-400" />
            <span className="font-display text-2xl">GATE Planner</span>
          </div>
          <h1 className="font-display text-5xl leading-tight mb-6">
            Crack GATE with<br />
            <span className="text-brand-400">AI-powered</span> study plans
          </h1>
          <p className="text-surface-400 text-lg max-w-md leading-relaxed">
            Personalized daily schedules, streak tracking, smart rescheduling,
            and study partner matching — all driven by AI.
          </p>
        </div>
        <div className="flex gap-6 text-surface-500 text-sm">
          <span>Trusted by 5,000+ aspirants</span>
          <span>•</span>
          <span>All GATE branches</span>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-10">
            <GraduationCap className="w-8 h-8 text-brand-500" />
            <span className="font-display text-xl text-surface-900">GATE Planner</span>
          </div>

          <h2 className="font-display text-3xl text-surface-900 mb-2">Welcome back</h2>
          <p className="text-surface-500 mb-8">Log in to continue your preparation</p>

          {authError && (
            <div className="mb-6 p-4 bg-danger-400/10 border border-danger-400/20 rounded-xl text-danger-600 text-sm">
              {authError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="label-text">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field"
                placeholder="you@example.com"
                required
              />
            </div>
            <div>
              <label className="label-text">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                placeholder="••••••••"
                required
                minLength={8}
              />
            </div>
            <button type="submit" disabled={authLoading} className="btn-primary w-full py-3">
              {authLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>Log in <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-surface-500">
            Don't have an account?{' '}
            <Link to="/signup" className="text-brand-600 font-semibold hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
