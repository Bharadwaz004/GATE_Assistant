/**
 * GATE exam constants — branches, subjects, and topic data.
 */

export const BRANCHES = [
  { value: 'CSE', label: 'Computer Science & IT' },
  { value: 'DA', label: 'Data Science & AI' },
  { value: 'ECE', label: 'Electronics & Communication' },
  { value: 'EE', label: 'Electrical Engineering' },
  { value: 'ME', label: 'Mechanical Engineering' },
  { value: 'CE', label: 'Civil Engineering' },
  { value: 'CH', label: 'Chemical Engineering' },
  { value: 'IN', label: 'Instrumentation Engineering' },
  { value: 'PI', label: 'Production & Industrial' },
  { value: 'BT', label: 'Biotechnology' },
  { value: 'MN', label: 'Mining Engineering' },
  { value: 'XE', label: 'Engineering Sciences' },
  { value: 'XL', label: 'Life Sciences' },
];

export const SUBJECTS_BY_BRANCH = {
  CSE: [
    'Engineering Mathematics', 'Digital Logic',
    'Computer Organization & Architecture',
    'Programming & Data Structures', 'Algorithms',
    'Theory of Computation', 'Compiler Design',
    'Operating Systems', 'Databases',
    'Computer Networks', 'Aptitude',
  ],
  DA: [
    'Probability and Statistics', 'Linear Algebra',
    'Calculus & Optimization',
    'Programming & Data Structures', 'Machine Learning',
    'AI', 'Databases & SQL', 'Aptitude',
  ],
  ECE: [
    'Engineering Mathematics', 'Networks, Signals & Systems',
    'Electronic Devices', 'Analog Circuits',
    'Digital Circuits', 'Control Systems',
    'Communications', 'Electromagnetics', 'Aptitude',
  ],
  EE: [
    'Engineering Mathematics', 'Electric Circuits',
    'Electromagnetic Fields', 'Signals & Systems',
    'Electrical Machines', 'Power Systems',
    'Control Systems', 'Power Electronics', 'Aptitude',
  ],
  ME: [
    'Engineering Mathematics', 'Applied Mechanics',
    'Strength of Materials', 'Thermodynamics',
    'Fluid Mechanics', 'Manufacturing',
    'Machine Design', 'Industrial Engineering', 'Aptitude',
  ],
};

// Fallback generic subjects for unmapped branches
export const DEFAULT_SUBJECTS = [
  'Engineering Mathematics',
  'Core Subject 1',
  'Core Subject 2',
  'Core Subject 3',
  'Aptitude',
];

export const getSubjectsForBranch = (branch) => {
  return SUBJECTS_BY_BRANCH[branch] || DEFAULT_SUBJECTS;
};

export const PREP_TYPES = [
  { value: 'coaching', label: 'Coaching Institute' },
  { value: 'self_study', label: 'Self Study' },
];
