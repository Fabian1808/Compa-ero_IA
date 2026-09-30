import type { Catalog } from '../types';
import { PRODUCT_NAME } from '../glossary';

/**
 * English (United States) message catalog.
 *
 * Placeholder for a future English release. It is intentionally not complete
 * yet: the runtime falls back to `es-PE` for any missing key, so shipping
 * English cannot produce blank labels while it is being written.
 *
 * English needs one form for every category because it has no grammatical
 * gender, but singular/plural agreement is still declared so the same keys are
 * reused verbatim when this catalog is completed.
 */
export const enUS: Catalog = {
  app: {
    name: PRODUCT_NAME,
    tagline: 'Your intelligent work companion',
    error: {
      title: 'Something went wrong',
      description: 'The app could not continue. Restart AI WORKMATE to try again.',
      details: 'Technical details',
    },
  },

  nav: {
    home: 'Home',
    myWork: 'My work',
    projects: 'Projects',
    people: 'People',
    calendar: 'Calendar',
    memory: 'Memory',
    connections: 'Connections',
    settings: 'Settings',
    open: 'Open menu',
    close: 'Close menu',
    main: 'Main navigation',
    userFallback: 'User',
  },

  admin: {
    section: 'Administration',
    dashboard: 'Administration panel',
    tenants: 'Teams',
    users: 'Users',
    metrics: 'Metrics',
    auditLogs: 'Audit log',
    settings: 'Settings',
    security: 'Security',
  },

  work: {
    states: {
      pending: 'Pending',
      inProgress: 'In progress',
      blocked: 'Blocked',
      waiting: 'Waiting for reply',
      needsDecision: 'Needs decision',
      completed: 'Completed',
    },
    counts: {
      tasks: {
        category: 'entity',
        forms: { zero: 'No tasks', one: '1 task', other: '{count} tasks' },
      },
      pending: {
        category: 'status',
        forms: { zero: 'Nothing pending', one: '1 pending', other: '{count} pending' },
      },
      blocked: {
        category: 'status',
        forms: { zero: 'No blockers', one: '1 blocker', other: '{count} blockers' },
      },
      decisions: {
        category: 'concept',
        forms: {
          zero: 'No decisions need your answer',
          one: '1 decision needs your answer',
          other: '{count} decisions need your answer',
        },
      },
      unread: {
        category: 'concept',
        forms: { zero: 'No updates', one: '1 update', other: '{count} updates' },
      },
      componentsReady: {
        category: 'entity',
        forms: { one: '1 component ready', other: '{count} components ready' },
      },
      source: {
        category: 'filter',
        forms: { one: '1 source', other: '{count} sources' },
      },
      availableAction: {
        category: 'action',
        forms: { zero: 'No actions available', one: '1 action available', other: '{count} actions available' },
      },
    },
    blockedByMe: 'Blocked by me',
    blockedByOthers: 'Blocked by others',
  },

  ai: {
    states: {
      detected: 'Detected',
      inferred: 'Inferred',
      suggested: 'Suggested',
      confirmed: 'Confirmed',
      executed: 'Executed',
    },
    origin: 'Origin',
    requiresConfirmation: 'Needs your confirmation',
    neverAutoExecuted: 'AI WORKMATE never acts on its own. It always asks you to confirm first.',
  },

  connections: {
    title: 'Connections',
    subtitle: 'Data sources AI WORKMATE can consult',
    outlook: 'Microsoft Outlook',
    teams: 'Microsoft Teams',
    oneDrive: 'Microsoft OneDrive',
    sharePoint: 'Microsoft SharePoint',
    excel: 'Microsoft Excel',
    powerBi: 'Microsoft Power BI',
    connect: 'Connect',
    disconnect: 'Disconnect',
    connected: 'Connected',
    notConnected: 'Not connected',
    scope: 'Requested permissions',
  },

  memory: {
    title: 'Memory',
    subtitle: 'Context AI WORKMATE remembers between sessions',
    storedLocally: 'Everything is saved on your computer',
    forget: 'Forget',
  },

  installer: {
    title: 'Setting up AI WORKMATE',
    checking: 'Checking your computer…',
    reviewTitle: 'Review what we will install',
    reviewSubtitle: 'AI WORKMATE installs what it needs to work offline. You can continue or cancel.',
    start: 'Install now',
    starting: 'Starting the installation…',
    installing: 'Installing components',
    installingShort: 'Installing…',
    ready: 'Ready',
    notReady: 'Pending',
    completeTitle: 'All set',
    completeSubtitle: 'AI WORKMATE is installed and ready to use',
    errorTitle: 'We could not finish the installation',
    unexpectedError: 'An unexpected error occurred',
    retry: 'Try again',
    cancel: 'Cancel',
    continueToOutlook: 'Connect Microsoft Outlook',
    progress: 'Progress',
    checkFailed: 'We could not check the required components',
    installFailed: 'We could not start the installation',
    components: {
      dataDir: {
        label: 'Data folder',
        description: 'Where your database, models and cache are stored',
      },
      database: {
        label: 'Local database',
        description: 'Stores your tasks, projects and context',
      },
      ollama: {
        label: 'Local AI engine',
        description: 'Lets AI WORKMATE work without sending your data to the internet',
      },
      chatModel: {
        label: 'Conversation model',
        description: 'The language model that replies and suggests next steps',
      },
      embeddingModel: {
        label: 'Search model',
        description: 'Finds information by meaning instead of exact words',
      },
    },
    steps: {
      dataDir: 'Preparing your data folder',
      database: 'Creating your local database',
      ollama: 'Installing the local AI engine',
      phi3: 'Downloading the conversation model',
      'nomic-embed': 'Downloading the search model',
    },
    stepChecking: 'Checking required components…',
    stepCheckComplete: 'Check complete',
    stepStarting: 'Starting the installation…',
    stepComplete: 'Installation complete',
    stepInstallingComponent: 'Installing the missing components…',
    stepComponentFailed: 'We could not install every component',
    stepDownloadingEngine: 'Downloading the local AI engine…',
    stepDownloadingModel: 'Downloading the models…',
    stepInstallingEngine: 'Installing the local AI engine…',
    stepStartingEngine: 'Starting the local AI engine…',
    stepDownloadFailed: 'We could not download the components',
    stepIntegrityFailed: 'The downloaded file did not match',
    stepUnverifiedDownload: 'No verified release is available',
    componentFailed: 'We could not install a component',
    errorUnverifiedDownload:
      'For safety, we only install the AI engine once the published release is verified.',
    errorIntegrityFailed: 'The downloaded file failed its integrity check.',
    errorDownloadFailed: 'We could not download the file. Check your internet connection.',
    errorModelFailed: 'We could not download the model.',
    alreadyInstalled: 'Everything required is already installed',
    started: 'Installation started',
    engineInstallStarted: 'We started installing the local AI engine',
    modelDownloadStarted: 'We started downloading the model',
    firstRunStarted: 'We started the initial setup',
    setupCompleted: 'Initial setup completed',
    checkComplete: 'Check complete',
    noAccountYet: 'You have not connected an account yet',
  },

  notifications: {
    saved: 'Saved',
    removed: 'Removed',
    synced: 'Synced',
    syncPending: 'Sync pending',
    actionNeedsConfirmation: 'AI WORKMATE wants to take an action. Review it before continuing.',
    connectionRestored: 'Connection restored',
    connectionLost: 'Cannot reach the server',
  },

  errors: {
    generic: 'Something did not go as expected. Try again.',
    network: 'We could not connect. Check your internet connection.',
    notFound: 'We could not find what you were looking for.',
    forbidden: 'You do not have permission to view this.',
    server: 'There is a server problem. Try again later.',
    timeout: 'The operation took too long. Try again.',
  },

  common: {
    loading: 'Loading…',
    save: 'Save',
    saving: 'Saving…',
    cancel: 'Cancel',
    confirm: 'Confirm',
    close: 'Close',
    back: 'Back',
    next: 'Next',
    previous: 'Previous',
    search: 'Search',
    filter: 'Filter',
    clear: 'Clear',
    apply: 'Apply',
    yes: 'Yes',
    no: 'No',
    today: 'Today',
    tomorrow: 'Tomorrow',
    yesterday: 'Yesterday',
    retry: 'Try again',
    seeAll: 'See all',
    empty: 'Nothing here yet',
  },

  privacy: {
    title: 'Privacy',
    localFirst: 'Your information is processed on this computer.',
    confirmBeforeActing: 'AI WORKMATE asks for confirmation before acting.',
    minimalData: 'We only store what is essential.',
    exportTitle: 'Export my data',
    deleteTitle: 'Delete my data',
  },
};