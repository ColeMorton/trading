import {
  faChartLine,
  faTable,
  faFileLines,
  faDownload,
  faSync,
  faRefresh,
  faSpinner,
  faExclamationTriangle,
  faInfoCircle,
  faCheckCircle,
  faTimesCircle,
  faFolder,
  faFolderOpen,
  faFile,
  faFileCsv,
  faEye,
  faEyeSlash,
  faBars,
  faSearch,
  faStar,
  faPlus,
  faMinus,
  faTrash,
  faCog,
  faWifi,
  faMobile,
  faDesktop,
  faBell,
  faUpload,
  faChevronUp,
  faChevronDown,
  faChevronLeft,
  faChevronRight,
  faSort,
  faSortUp,
  faSortDown,
  faFilter,
  faCalculator,
  faBriefcase,
  faFileExport,
  faCheckSquare,
  faSquare,
  faEdit,
  faSave,
  faUndo,
  faRedo,
  faTimes,
  faColumns,
  faCopyright,
  faUniversalAccess,
  faClock,
  faCode,
  faFlask,
  faList
} from '@fortawesome/free-solid-svg-icons';

// Navigation icons
export const navigationIcons = {
  brand: faChartLine,
  menu: faBars,
  search: faSearch,
  times: faTimes,
} as const;

// Data and file icons
export const dataIcons = {
  table: faTable,
  file: faFile,
  fileCsv: faFileCsv,
  folder: faFolder,
  folderOpen: faFolderOpen,
  textView: faFileLines,
  columns: faColumns,
  code: faCode,
  list: faList,
} as const;

// Action icons
export const actionIcons = {
  download: faDownload,
  upload: faUpload,
  refresh: faRefresh,
  sync: faSync,
  add: faPlus,
  remove: faMinus,
  delete: faTrash,
  edit: faEdit,
  save: faSave,
  undo: faUndo,
  redo: faRedo,
  export: faFileExport,
} as const;

// Status and feedback icons
export const statusIcons = {
  loading: faSpinner,
  success: faCheckCircle,
  error: faTimesCircle,
  warning: faExclamationTriangle,
  info: faInfoCircle,
  star: faStar,
  lastUpdated: faClock,
} as const;

// View and display icons
export const viewIcons = {
  show: faEye,
  hide: faEyeSlash,
  chevronUp: faChevronUp,
  chevronDown: faChevronDown,
  chevronLeft: faChevronLeft,
  chevronRight: faChevronRight,
} as const;

// Table and sorting icons
export const tableIcons = {
  sort: faSort,
  sortUp: faSortUp,
  sortDown: faSortDown,
  filter: faFilter,
  selectAll: faCheckSquare,
  deselect: faSquare,
} as const;

// Connectivity and PWA icons
export const connectivityIcons = {
  online: faWifi,
  offline: faTimesCircle, // Using times-circle as offline indicator
  mobile: faMobile,
  desktop: faDesktop,
  notification: faBell,
} as const;

// Portfolio and analysis icons
export const portfolioIcons = {
  portfolio: faBriefcase,
  calculator: faCalculator,
  settings: faCog,
  parameterTesting: faFlask,
} as const;

// Accessibility and UI icons
export const uiIcons = {
  copyright: faCopyright,
  skipLink: faUniversalAccess,
} as const;

// Export all icons in a single object for easy access
export const icons = {
  ...navigationIcons,
  ...dataIcons,
  ...actionIcons,
  ...statusIcons,
  ...viewIcons,
  ...tableIcons,
  ...connectivityIcons,
  ...portfolioIcons,
  ...uiIcons,
} as const;