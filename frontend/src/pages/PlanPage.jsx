import React, { useEffect, useState } from 'react';
import {
  Calendar, Zap, Loader2, ChevronLeft, ChevronRight,
  BookOpen, Target, BarChart3, Clock, CheckCircle2, SkipForward,
} from 'lucide-react';
import clsx from 'clsx';
import useStore from '../store/useStore';

const TASK_TYPE_STYLES = {
  study:     { icon: BookOpen, color: 'bg-blue-50 text-blue-600 border-blue-200' },
  revision:  { icon: Zap,      color: 'bg-amber-50 text-amber-600 border-amber-200' },
  mock_test: { icon: Target,   color: 'bg-purple-50 text-purple-600 border-purple-200' },
  practice:  { icon: BarChart3, color: 'bg-emerald-50 text-emerald-600 border-emerald-200' },
};

export default function PlanPage() {
  const {
    weeklyPlan, generatePlan, fetchDailyPlan, updateTask,
    dailyPlan, planLoading,
  } = useStore();
  const [weekNum, setWeekNum] = useState(1);
  const [selectedDay, setSelectedDay] = useState(0);
  const [generating, setGenerating] = useState(false);
  const [taskLoading, setTaskLoading] = useState(null);

  useEffect(() => {
    if (!weeklyPlan) {
      handleGenerate();
    }
  }, []);

  const handleGenerate = async (force = false) => {
    setGenerating(true);
    try {
      await generatePlan(weekNum, force);
    } catch {}
    setGenerating(false);
  };

  const handleTaskAction = async (taskId, status) => {
    setTaskLoading(taskId);
    try {
      await updateTask(taskId, status);
      // Refresh if viewing current day
      await fetchDailyPlan();
    } catch {}
    setTaskLoading(null);
  };

  const currentDay = weeklyPlan?.days?.[selectedDay];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl text-surface-900">Study Plan</h1>
          <p className="text-surface-500 mt-1">
            {weeklyPlan
              ? `Week ${weeklyPlan.week_number}: ${weeklyPlan.start_date} → ${weeklyPlan.end_date}`
              : 'Generate your personalized plan'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 bg-surface-100 rounded-xl p-1">
            <button
              onClick={() => setWeekNum((w) => Math.max(1, w - 1))}
              className="p-2 rounded-lg hover:bg-white transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-3 text-sm font-semibold text-surface-700">
              Week {weekNum}
            </span>
            <button
              onClick={() => setWeekNum((w) => w + 1)}
              className="p-2 rounded-lg hover:bg-white transition-colors"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
          <button
            onClick={() => handleGenerate(true)}
            disabled={generating}
            className="btn-brand"
          >
            {generating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Zap className="w-4 h-4" />
                {weeklyPlan ? 'Regenerate' : 'Generate Plan'}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Loading state */}
      {(planLoading || generating) && !weeklyPlan && (
        <div className="glass-card p-16 text-center">
          <Loader2 className="w-10 h-10 animate-spin text-brand-500 mx-auto mb-4" />
          <h3 className="font-display text-xl text-surface-700 mb-2">Generating your plan...</h3>
          <p className="text-surface-400">Our AI is crafting a personalized study schedule for you</p>
        </div>
      )}

      {/* Weekly Plan View */}
      {weeklyPlan && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Day Selector (sidebar) */}
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-surface-500 uppercase tracking-wide mb-3">
              Days
            </h3>
            {weeklyPlan.days.map((day, i) => {
              const totalTasks = day.tasks?.length || 0;
              const completed = day.tasks?.filter((t) => t.status === 'completed').length || 0;

              return (
                <button
                  key={i}
                  onClick={() => setSelectedDay(i)}
                  className={clsx(
                    'w-full p-3.5 rounded-xl text-left transition-all duration-200',
                    selectedDay === i
                      ? 'bg-brand-500 text-white shadow-elevated'
                      : 'glass-card-hover text-surface-700'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold text-sm">{day.day}</div>
                      {day.date && (
                        <div className={clsx(
                          'text-xs mt-0.5',
                          selectedDay === i ? 'text-white/70' : 'text-surface-400'
                        )}>
                          {new Date(day.date + 'T00:00:00').toLocaleDateString('en-US', {
                            weekday: 'short', month: 'short', day: 'numeric'
                          })}
                        </div>
                      )}
                    </div>
                    <div className={clsx(
                      'text-xs font-mono font-bold',
                      selectedDay === i ? 'text-white/80' : 'text-surface-400'
                    )}>
                      {completed}/{totalTasks}
                    </div>
                  </div>
                  {/* Mini progress bar */}
                  <div className={clsx(
                    'h-1 rounded-full mt-2',
                    selectedDay === i ? 'bg-white/20' : 'bg-surface-100'
                  )}>
                    <div
                      className={clsx(
                        'h-full rounded-full transition-all',
                        selectedDay === i ? 'bg-white/60' : 'bg-brand-400'
                      )}
                      style={{ width: `${totalTasks > 0 ? (completed / totalTasks) * 100 : 0}%` }}
                    />
                  </div>
                </button>
              );
            })}
          </div>

          {/* Day Detail */}
          <div className="lg:col-span-3">
            {currentDay ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="font-display text-xl text-surface-900">
                    {currentDay.day}
                    {currentDay.date && (
                      <span className="text-surface-400 font-body text-base ml-2">
                        {currentDay.date}
                      </span>
                    )}
                  </h2>
                  {currentDay.total_hours && (
                    <span className="text-sm text-surface-500 flex items-center gap-1">
                      <Clock className="w-4 h-4" /> {currentDay.total_hours}h total
                    </span>
                  )}
                </div>

                <div className="space-y-3">
                  {currentDay.tasks.map((task, j) => {
                    const style = TASK_TYPE_STYLES[task.task_type] || TASK_TYPE_STYLES.study;
                    const TypeIcon = style.icon;

                    return (
                      <div
                        key={task.id || j}
                        className={clsx(
                          'glass-card p-4 border-l-4 transition-all animate-slide-right',
                          task.status === 'completed' ? 'border-l-success-500 opacity-60' :
                          task.status === 'skipped' ? 'border-l-surface-300 opacity-50' :
                          'border-l-brand-400'
                        )}
                        style={{ animationDelay: `${j * 50}ms` }}
                      >
                        <div className="flex items-start gap-3">
                          <div className={clsx('p-2 rounded-lg border', style.color)}>
                            <TypeIcon className="w-4 h-4" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-semibold text-surface-900">{task.subject}</span>
                              <span className={clsx(
                                'text-xs px-2 py-0.5 rounded-full font-medium border',
                                style.color
                              )}>
                                {task.task_type.replace('_', ' ')}
                              </span>
                            </div>
                            <p className="text-sm text-surface-600 mt-0.5">{task.topic}</p>
                            {task.subtopic && (
                              <p className="text-xs text-surface-400 mt-0.5">{task.subtopic}</p>
                            )}
                            <div className="flex items-center gap-4 mt-2 text-xs text-surface-400">
                              <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" /> {task.duration}
                              </span>
                              {task.timing && <span>{task.timing}</span>}
                            </div>
                          </div>

                          {task.id && task.status === 'pending' && (
                            <div className="flex gap-1.5 flex-shrink-0">
                              <button
                                onClick={() => handleTaskAction(task.id, 'completed')}
                                disabled={taskLoading === task.id}
                                className="p-2 rounded-lg bg-success-500/10 text-success-600 hover:bg-success-500/20 transition-colors"
                              >
                                <CheckCircle2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleTaskAction(task.id, 'skipped')}
                                disabled={taskLoading === task.id}
                                className="p-2 rounded-lg bg-surface-100 text-surface-400 hover:bg-surface-200 transition-colors"
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
                  })}
                </div>
              </div>
            ) : (
              <div className="glass-card p-12 text-center">
                <Calendar className="w-12 h-12 text-surface-300 mx-auto mb-4" />
                <p className="text-surface-500">Select a day to view tasks</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
