import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  GraduationCap, ArrowRight, ArrowLeft, Loader2,
  BookOpen, Clock, Target, CheckCircle2,
} from 'lucide-react';
import clsx from 'clsx';
import useStore from '../store/useStore';
import { BRANCHES, PREP_TYPES, getSubjectsForBranch } from '../utils/constants';

const STEPS = ['Branch', 'Preparation', 'Schedule', 'Subjects'];

export default function OnboardingPage() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    branch: '',
    prep_type: '',
    target_exam_date: '',
    coaching_start_time: '',
    coaching_end_time: '',
    daily_available_hours: 6,
    subjects: [],
  });

  const { submitOnboarding, profileLoading } = useStore();
  const navigate = useNavigate();

  const update = (key, val) => setForm((f) => ({ ...f, [key]: val }));

  const toggleSubject = (subj) => {
    setForm((f) => ({
      ...f,
      subjects: f.subjects.includes(subj)
        ? f.subjects.filter((s) => s !== subj)
        : [...f.subjects, subj],
    }));
  };

  const canNext = () => {
    switch (step) {
      case 0: return !!form.branch;
      case 1: return !!form.prep_type && !!form.target_exam_date;
      case 2:
        if (form.prep_type === 'coaching') {
          return !!form.coaching_start_time && !!form.coaching_end_time;
        }
        return form.daily_available_hours > 0;
      case 3: return form.subjects.length > 0;
      default: return false;
    }
  };

  const handleSubmit = async () => {
    try {
      await submitOnboarding(form);
      navigate('/');
    } catch (err) {
      console.error('Onboarding failed:', err);
    }
  };

  const availableSubjects = form.branch ? getSubjectsForBranch(form.branch) : [];

  return (
    <div className="min-h-screen bg-surface-50 flex flex-col">
      {/* Header */}
      <header className="flex items-center gap-3 px-8 h-16 border-b border-surface-200">
        <GraduationCap className="w-7 h-7 text-brand-500" />
        <span className="font-display text-lg text-surface-900">GATE Planner</span>
      </header>

      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-2xl">
          {/* Step indicator */}
          <div className="flex items-center justify-center gap-2 mb-10">
            {STEPS.map((label, i) => (
              <React.Fragment key={label}>
                <div className="flex items-center gap-2">
                  <div
                    className={clsx(
                      'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all',
                      i < step && 'bg-success-500 text-white',
                      i === step && 'bg-brand-500 text-white',
                      i > step && 'bg-surface-200 text-surface-400'
                    )}
                  >
                    {i < step ? <CheckCircle2 className="w-4 h-4" /> : i + 1}
                  </div>
                  <span className={clsx(
                    'text-sm font-medium hidden sm:inline',
                    i === step ? 'text-surface-900' : 'text-surface-400'
                  )}>
                    {label}
                  </span>
                </div>
                {i < STEPS.length - 1 && (
                  <div className={clsx(
                    'w-8 h-0.5 rounded',
                    i < step ? 'bg-success-500' : 'bg-surface-200'
                  )} />
                )}
              </React.Fragment>
            ))}
          </div>

          {/* Step content */}
          <div className="glass-card p-8 animate-fade-in">
            {/* Step 0: Branch */}
            {step === 0 && (
              <div>
                <h2 className="font-display text-2xl mb-2">Select your GATE branch</h2>
                <p className="text-surface-500 mb-6">Choose the paper you're preparing for</p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {BRANCHES.map(({ value, label }) => (
                    <button
                      key={value}
                      onClick={() => update('branch', value)}
                      className={clsx(
                        'p-4 rounded-xl border-2 text-left transition-all duration-200',
                        form.branch === value
                          ? 'border-brand-500 bg-brand-50 text-brand-700'
                          : 'border-surface-200 hover:border-surface-300 text-surface-700'
                      )}
                    >
                      <div className="font-bold text-lg">{value}</div>
                      <div className="text-xs text-surface-500 mt-0.5 leading-tight">{label}</div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Step 1: Prep type + exam date */}
            {step === 1 && (
              <div>
                <h2 className="font-display text-2xl mb-2">How are you preparing?</h2>
                <p className="text-surface-500 mb-6">This helps us structure your plan</p>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  {PREP_TYPES.map(({ value, label }) => (
                    <button
                      key={value}
                      onClick={() => update('prep_type', value)}
                      className={clsx(
                        'p-5 rounded-xl border-2 text-center transition-all',
                        form.prep_type === value
                          ? 'border-brand-500 bg-brand-50'
                          : 'border-surface-200 hover:border-surface-300'
                      )}
                    >
                      {value === 'coaching' ? (
                        <BookOpen className="w-8 h-8 mx-auto mb-2 text-brand-500" />
                      ) : (
                        <Target className="w-8 h-8 mx-auto mb-2 text-brand-500" />
                      )}
                      <div className="font-semibold">{label}</div>
                    </button>
                  ))}
                </div>

                <div>
                  <label className="label-text">Target GATE Exam Date</label>
                  <input
                    type="date"
                    value={form.target_exam_date}
                    onChange={(e) => update('target_exam_date', e.target.value)}
                    className="input-field"
                    min={new Date().toISOString().split('T')[0]}
                  />
                </div>
              </div>
            )}

            {/* Step 2: Schedule */}
            {step === 2 && (
              <div>
                <h2 className="font-display text-2xl mb-2">Your study schedule</h2>

                {form.prep_type === 'coaching' ? (
                  <div className="space-y-5">
                    <p className="text-surface-500 mb-4">Tell us about your coaching timings</p>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="label-text">Coaching starts at</label>
                        <input
                          type="time"
                          value={form.coaching_start_time}
                          onChange={(e) => update('coaching_start_time', e.target.value)}
                          className="input-field"
                        />
                      </div>
                      <div>
                        <label className="label-text">Coaching ends at</label>
                        <input
                          type="time"
                          value={form.coaching_end_time}
                          onChange={(e) => update('coaching_end_time', e.target.value)}
                          className="input-field"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="label-text">Available self-study hours (after coaching)</label>
                      <input
                        type="range"
                        min="1" max="10" step="0.5"
                        value={form.daily_available_hours}
                        onChange={(e) => update('daily_available_hours', parseFloat(e.target.value))}
                        className="w-full accent-brand-500"
                      />
                      <div className="flex justify-between text-sm text-surface-500 mt-1">
                        <span>1 hr</span>
                        <span className="font-bold text-brand-600">{form.daily_available_hours} hrs/day</span>
                        <span>10 hrs</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div>
                    <p className="text-surface-500 mb-6">How many hours can you study daily?</p>
                    <div className="flex items-center gap-6 mb-4">
                      <Clock className="w-10 h-10 text-brand-400" />
                      <div className="flex-1">
                        <input
                          type="range"
                          min="1" max="14" step="0.5"
                          value={form.daily_available_hours}
                          onChange={(e) => update('daily_available_hours', parseFloat(e.target.value))}
                          className="w-full accent-brand-500"
                        />
                        <div className="flex justify-between text-sm text-surface-500 mt-1">
                          <span>1 hr</span>
                          <span className="text-lg font-bold text-brand-600">{form.daily_available_hours} hrs/day</span>
                          <span>14 hrs</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Step 3: Subjects */}
            {step === 3 && (
              <div>
                <h2 className="font-display text-2xl mb-2">Pick your subjects</h2>
                <p className="text-surface-500 mb-6">
                  Select the subjects you want in your plan ({form.subjects.length} selected)
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {availableSubjects.map((subj) => (
                    <button
                      key={subj}
                      onClick={() => toggleSubject(subj)}
                      className={clsx(
                        'p-3.5 rounded-xl border-2 text-left text-sm font-medium transition-all',
                        form.subjects.includes(subj)
                          ? 'border-brand-500 bg-brand-50 text-brand-700'
                          : 'border-surface-200 hover:border-surface-300 text-surface-600'
                      )}
                    >
                      <div className="flex items-center gap-2">
                        <div className={clsx(
                          'w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all',
                          form.subjects.includes(subj)
                            ? 'bg-brand-500 border-brand-500'
                            : 'border-surface-300'
                        )}>
                          {form.subjects.includes(subj) && (
                            <CheckCircle2 className="w-3.5 h-3.5 text-white" />
                          )}
                        </div>
                        {subj}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Navigation buttons */}
          <div className="flex justify-between mt-6">
            <button
              onClick={() => setStep((s) => s - 1)}
              disabled={step === 0}
              className="btn-outline"
            >
              <ArrowLeft className="w-4 h-4" /> Back
            </button>

            {step < STEPS.length - 1 ? (
              <button
                onClick={() => setStep((s) => s + 1)}
                disabled={!canNext()}
                className="btn-primary"
              >
                Continue <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={!canNext() || profileLoading}
                className="btn-brand"
              >
                {profileLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>Start Planning <ArrowRight className="w-4 h-4" /></>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
