import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Flame, TrendingUp, Clock, CheckCircle2, BookOpen,
  Zap, Calendar, ArrowRight, Users, Loader2, SkipForward,
  BarChart3, Target,
} from 'lucide-react';
import clsx from 'clsx';
import useStore from '../store/useStore';

// ── Stat Card ───────────────────────────────────────────────
function StatCard({ icon: Icon, label, value, accent, sub, delay }) {
  return (
    <div className={clsx('glass-card-hover p-5 animate-slide-up', delay)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-surface-500 font-medium">{label}</p>
          <p className={clsx('text-3xl font-bold mt-1 tracking-tight', accent || 'text-surface-900')}>
            {value}
          </p>
          {sub && <p className="text-xs text-surface-400 mt-1">{sub}</p>}
        </div>
        <div className={clsx('p-2.5 rounded-xl', accent ? 'bg-brand-100' : 'bg-surface-100')}>
          <Icon className={clsx('w-5 h-5', accent ? 'text-brand-600' : 'text-surface-500')} />
        </div>
      </div>
    </div>
  );
}

// ── Task Card ───────────────────────────────────────────────
function TaskCard({ task, onComplete, onSkip, loading }) {
  const statusColors = {
    pending: 'border-l-brand-400',
    completed: 'border-l-success-500',
    skipped: 'border-l-surface-300',
  };
  const typeIcons = {
    study: BookOpen,
    revision: Zap,
    mock_test: Target,
    practice: BarChart3,
  };
  const TypeIcon = typeIcons[task.task_type] || BookOpen;

  return (
    <div className={clsx(
      'glass-card-hover p-4 border-l-4 transition-all',
      statusColors[task.status] || 'border-l-brand-400',
      task.status === 'completed' && 'opacity-60'
    )}>
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-brand-50 mt-0.5">
          <TypeIcon className="w-4 h-4 text-brand-600" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-surface-900">{task.subject}</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-surface-100 text-surface-500 font-medium">
              {task.task_type}
            </span>
          </div>
          <p className="text-sm text-surface-600 mt-0.5">{task.topic}</p>
          {task.subtopic && (
            <p className="text-xs text-surface-400 mt-0.5">{task.subtopic}</p>
          )}
          <div className="flex items-center gap-3 mt-2 text-xs text-surface-400">
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" /> {task.duration}
            </span>
            {task.timing && <span>{task.timing}</span>}
          </div>
        </div>

        {/* Actions */}
        {task.status === 'pending' && (
          <div className="flex gap-1.5 flex-shrink-0">
            <button
              onClick={() => onComplete(task.id)}
              disabled={loading}
              className="p-2 rounded-lg bg-success-500/10 text-success-600 hover:bg-success-500/20 transition-colors"
              title="Complete"
            >
              <CheckCircle2 className="w-4 h-4" />
            </button>
            <button
              onClick={() => onSkip(task.id)}
              disabled={loading}
              className="p-2 rounded-lg bg-surface-100 text-surface-400 hover:bg-surface-200 transition-colors"
              title="Skip"
            >
              <SkipForward className="w-4 h-4" />
            </button>
          </div>
        )}
        {task.status === 'completed' && (
          <CheckCircle2 className="w-5 h-5 text-success-500 flex-shrink-0" />
        )}
      </div>
    </div>
  );
}

// ── Progress Ring ───────────────────────────────────────────
function ProgressRing({ percent, size = 80, stroke = 6 }) {
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percent / 100) * circumference;

  return (
    <svg width={size} height={size} className="-rotate-90">
      <circle
        cx={size / 2} cy={size / 2} r={radius}
        fill="none" stroke="#e7e5e4" strokeWidth={stroke}
      />
      <circle
        cx={size / 2} cy={size / 2} r={radius}
        fill="none" stroke="#e85a10" strokeWidth={stroke}
        strokeDasharray={circumference} strokeDashoffset={offset}
        strokeLinecap="round"
        className="transition-all duration-700 ease-out"
      />
    </svg>
  );
}

// ── Main Dashboard ──────────────────────────────────────────
export default function DashboardPage() {
  const {
    profile, dailyPlan, streak, progress,
    fetchDailyPlan, fetchStreak, fetchProgress, fetchMatches,
    updateTask, generatePlan, matches,
    planLoading, progressLoading,
  } = useStore();
  const navigate = useNavigate();
  const [taskLoading, setTaskLoading] = useState(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchDailyPlan().catch(() => {});
    fetchStreak().catch(() => {});
    fetchProgress().catch(() => {});
    fetchMatches(5).catch(() => {});
  }, []);

  const handleComplete = async (taskId) => {
    setTaskLoading(taskId);
    try { await updateTask(taskId, 'completed'); } catch {}
    setTaskLoading(null);
  };

  const handleSkip = async (taskId) => {
    setTaskLoading(taskId);
    try { await updateTask(taskId, 'skipped'); } catch {}
    setTaskLoading(null);
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await generatePlan(1);
      await fetchDailyPlan();
    } catch {}
    setGenerating(false);
  };

  const todayStr = new Date().toLocaleDateString('en-US', {
    weekday: 'long', month: 'long', day: 'numeric',
  });

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Greeting */}
      <div>
        <h1 className="font-display text-3xl text-surface-900">
          {profile ? `Hey, ${profile.full_name.split(' ')[0]}` : 'Dashboard'}
        </h1>
        <p className="text-surface-500 mt-1">{todayStr}</p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Flame}
          label="Current Streak"
          value={`${streak?.current_streak || 0}`}
          sub={`Longest: ${streak?.longest_streak || 0} days`}
          accent
          delay="stagger-1"
        />
        <StatCard
          icon={CheckCircle2}
          label="Tasks Completed"
          value={progress?.completed_tasks || 0}
          sub={`${progress?.completion_rate || 0}% completion`}
          delay="stagger-2"
        />
        <StatCard
          icon={Clock}
          label="Study Hours"
          value={`${progress?.total_study_hours || 0}h`}
          sub="Total tracked"
          delay="stagger-3"
        />
        <StatCard
          icon={TrendingUp}
          label="Total Tasks"
          value={progress?.total_tasks || 0}
          sub={`${progress?.skipped_tasks || 0} skipped`}
          delay="stagger-4"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* ── Today's Plan ─────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-xl text-surface-900">Today's Plan</h2>
            {dailyPlan && (
              <div className="flex items-center gap-3">
                <div className="relative">
                  <ProgressRing percent={dailyPlan.completion_rate} size={48} stroke={4} />
                  <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-surface-700">
                    {Math.round(dailyPlan.completion_rate)}%
                  </span>
                </div>
                <div className="text-sm">
                  <div className="font-semibold text-surface-700">{dailyPlan.total_hours}h planned</div>
                  <div className="text-surface-400">{dailyPlan.tasks?.length || 0} tasks</div>
                </div>
              </div>
            )}
          </div>

          {planLoading && !dailyPlan ? (
            <div className="glass-card p-12 flex items-center justify-center">
              <Loader2 className="w-6 h-6 animate-spin text-brand-500" />
            </div>
          ) : dailyPlan?.tasks?.length > 0 ? (
            <div className="space-y-3">
              {dailyPlan.tasks.map((task, i) => (
                <div key={task.id || i} className={clsx('animate-slide-right', `stagger-${i + 1}`)}>
                  <TaskCard
                    task={task}
                    onComplete={handleComplete}
                    onSkip={handleSkip}
                    loading={taskLoading === task.id}
                  />
                </div>
              ))}
            </div>
          ) : (
            <div className="glass-card p-10 text-center">
              <Calendar className="w-12 h-12 text-surface-300 mx-auto mb-4" />
              <h3 className="font-display text-xl text-surface-700 mb-2">No plan for today</h3>
              <p className="text-surface-400 mb-6 max-w-sm mx-auto">
                Generate your first AI-powered study plan to get started
              </p>
              <button onClick={handleGenerate} disabled={generating} className="btn-brand">
                {generating ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>Generate Week 1 Plan <Zap className="w-4 h-4" /></>
                )}
              </button>
            </div>
          )}
        </div>

        {/* ── Sidebar: Subject Progress + Partners ─────────── */}
        <div className="space-y-6">
          {/* Subject Progress */}
          {progress?.subject_progress && Object.keys(progress.subject_progress).length > 0 && (
            <div className="glass-card p-5">
              <h3 className="font-display text-lg text-surface-900 mb-4">Subject Progress</h3>
              <div className="space-y-3">
                {Object.entries(progress.subject_progress).map(([subj, data]) => (
                  <div key={subj}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-surface-700 font-medium truncate">{subj}</span>
                      <span className="text-surface-500">{data.rate}%</span>
                    </div>
                    <div className="h-2 bg-surface-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-brand-500 rounded-full transition-all duration-700"
                        style={{ width: `${data.rate}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Study Partners */}
          <div className="glass-card p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display text-lg text-surface-900">Study Partners</h3>
              <button
                onClick={() => navigate('/matches')}
                className="text-xs text-brand-600 font-semibold hover:underline flex items-center gap-1"
              >
                View all <ArrowRight className="w-3 h-3" />
              </button>
            </div>
            {matches?.matches?.length > 0 ? (
              <div className="space-y-3">
                {matches.matches.slice(0, 3).map((m) => (
                  <div key={m.user_id} className="flex items-center gap-3 p-2.5 rounded-xl hover:bg-surface-50 transition-colors">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                      {m.full_name[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-semibold text-surface-900 truncate">{m.full_name}</div>
                      <div className="text-xs text-surface-400">
                        {m.branch} • {Math.round(m.similarity_score * 100)}% match
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4">
                <Users className="w-8 h-8 text-surface-300 mx-auto mb-2" />
                <p className="text-sm text-surface-400">No matches yet</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
