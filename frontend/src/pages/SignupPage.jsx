import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { GraduationCap, ArrowRight, Loader2 } from 'lucide-react';
import useStore from '../store/useStore';

export default function SignupPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { signup, authLoading, authError } = useStore();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await signup(email, password, fullName);
      navigate('/onboarding');
    } catch {}
  };

  return (
    <div className="min-h-screen flex">
      {/* Left branding panel */}
      <div className="hidden lg:flex lg:w-1/2 bg-surface-950 text-white flex-col justify-between p-12">
        <div>
          <div className="flex items-center gap-3 mb-16">
            <GraduationCap className="w-9 h-9 text-brand-400" />
            <span className="font-display text-2xl">GATE Planner</span>
          </div>
          <h1 className="font-display text-5xl leading-tight mb-6">
            Your GATE journey<br />
            <span className="text-brand-400">starts here</span>
          </h1>
          <p className="text-surface-400 text-lg max-w-md leading-relaxed">
            Join thousands of aspirants who use AI to plan smarter, study consistently, and track their progress toward GATE success.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-4 text-center">
          {[
            { n: '12+', label: 'Branches' },
            { n: 'AI', label: 'Powered Plans' },
            { n: '∞', label: 'Rescheduling' },
          ].map((s) => (
            <div key={s.label} className="p-4 rounded-xl bg-white/5">
              <div className="text-2xl font-bold text-brand-400">{s.n}</div>
              <div className="text-xs text-surface-400 mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-10">
            <GraduationCap className="w-8 h-8 text-brand-500" />
            <span className="font-display text-xl text-surface-900">GATE Planner</span>
          </div>

          <h2 className="font-display text-3xl text-surface-900 mb-2">Create your account</h2>
          <p className="text-surface-500 mb-8">Start your GATE preparation journey</p>

          {authError && (
            <div className="mb-6 p-4 bg-danger-400/10 border border-danger-400/20 rounded-xl text-danger-600 text-sm">
              {authError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="label-text">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="input-field"
                placeholder="Sai Chandana"
                required
                minLength={2}
              />
            </div>
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
                placeholder="Minimum 8 characters"
                required
                minLength={8}
              />
            </div>
            <button type="submit" disabled={authLoading} className="btn-primary w-full py-3">
              {authLoading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>Create Account <ArrowRight className="w-4 h-4" /></>
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-surface-500">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-600 font-semibold hover:underline">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
