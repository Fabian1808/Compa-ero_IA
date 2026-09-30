import type { Catalog } from '../types';
import { PRODUCT_NAME, PRODUCT_TAGLINE } from '../glossary';

/**
 * Spanish (Peru) message catalog — the default and source locale.
 *
 * Every user-visible string in the app belongs here. Technical values such as
 * file paths, model names, URLs and error codes must never be added as
 * translatable text: they are not part of the user's language.
 */
export const esPE: Catalog = {
  app: {
    name: PRODUCT_NAME,
    tagline: PRODUCT_TAGLINE,
    error: {
      title: 'Ocurrió un problema',
      description: 'La aplicación no pudo continuar. Reinicia AI WORKMATE para intentarlo de nuevo.',
      details: 'Detalle técnico',
    },
  },

  nav: {
    home: 'Inicio',
    myWork: 'Mi trabajo',
    projects: 'Proyectos',
    people: 'Personas',
    calendar: 'Calendario',
    memory: 'Memoria',
    connections: 'Conexiones',
    settings: 'Configuración',
    open: 'Abrir menú',
    close: 'Cerrar menú',
    main: 'Navegación principal',
    userFallback: 'Usuario',
  },

  admin: {
    section: 'Administración',
    dashboard: 'Panel de administración',
    tenants: 'Equipos',
    users: 'Personas usuarias',
    metrics: 'Métricas',
    auditLogs: 'Registro de auditoría',
    settings: 'Configuración',
    security: 'Seguridad',
  },

  work: {
    states: {
      pending: 'Pendiente',
      inProgress: 'En curso',
      blocked: 'Bloqueado',
      waiting: 'Esperando respuesta',
      needsDecision: 'Requiere decisión',
      completed: 'Completada',
    },
    counts: {
      tasks: {
        category: 'entity',
        forms: {
          zero: 'Sin tareas',
          one: '1 tarea',
          other: '{count} tareas',
        },
      },
      pending: {
        category: 'status',
        forms: {
          zero: 'Nada pendiente',
          one: '1 pendiente',
          other: '{count} pendientes',
        },
      },
      blocked: {
        category: 'status',
        forms: {
          zero: 'Sin bloqueos',
          one: '1 bloqueo',
          other: '{count} bloqueos',
        },
      },
      decisions: {
        category: 'concept',
        forms: {
          zero: 'Sin decisiones pendientes',
          one: '1 decisión requiere tu respuesta',
          other: '{count} decisiones requieren tu respuesta',
        },
      },
      unread: {
        category: 'concept',
        forms: {
          zero: 'Sin novedades',
          one: '1 novedad',
          other: '{count} novedades',
        },
      },
      componentsReady: {
        category: 'entity',
        forms: {
          one: '1 componente listo',
          other: '{count} componentes listos',
        },
      },
      source: {
        category: 'filter',
        forms: {
          one: '1 origen',
          other: '{count} orígenes',
        },
      },
      availableAction: {
        category: 'action',
        forms: {
          zero: 'No hay acciones disponibles',
          one: 'Hay 1 acción disponible',
          other: 'Hay {count} acciones disponibles',
        },
      },
    },
    blockedByMe: 'Bloqueada por mí',
    blockedByOthers: 'Bloqueada por otras personas',
  },

  ai: {
    states: {
      detected: 'Detectado',
      inferred: 'Inferido',
      suggested: 'Sugerido',
      confirmed: 'Confirmado',
      executed: 'Ejecutado',
    },
    origin: 'Origen',
    requiresConfirmation: 'Requiere tu confirmación',
    neverAutoExecuted:
      'AI WORKMATE nunca ejecuta una acción por su cuenta. Siempre te pide confirmación primero.',
  },

  connections: {
    title: 'Conexiones',
    subtitle: 'Fuentes de datos que AI WORKMATE puede consultar',
    outlook: 'Microsoft Outlook',
    teams: 'Microsoft Teams',
    oneDrive: 'Microsoft OneDrive',
    sharePoint: 'Microsoft SharePoint',
    excel: 'Microsoft Excel',
    powerBi: 'Microsoft Power BI',
    connect: 'Conectar',
    disconnect: 'Desconectar',
    connected: 'Conectado',
    notConnected: 'Sin conectar',
    scope: 'Permisos solicitados',
  },

  memory: {
    title: 'Memoria',
    subtitle: 'Contexto que AI WORKMATE recuerda entre sesiones',
    storedLocally: 'Todo se guarda en tu equipo',
    forget: 'Olvidar',
  },

  installer: {
    title: 'Preparando AI WORKMATE',
    checking: 'Comprobando tu equipo…',
    reviewTitle: 'Revisa lo que vamos a instalar',
    reviewSubtitle:
      'AI WORKMATE instala lo necesario para funcionar sin conexión. Puedes continuar o cancelar.',
    start: 'Instalar ahora',
    starting: 'Iniciando la instalación…',
    installing: 'Instalando componentes',
    installingShort: 'Instalando…',
    ready: 'Listo',
    notReady: 'Pendiente',
    completeTitle: 'Todo listo',
    completeSubtitle: 'AI WORKMATE está instalado y listo para usar',
    errorTitle: 'No pudimos completar la instalación',
    unexpectedError: 'Ocurrió un error inesperado',
    retry: 'Reintentar',
    cancel: 'Cancelar',
    continueToOutlook: 'Conectar Microsoft Outlook',
    progress: 'Progreso',
    checkFailed: 'No pudimos comprobar los componentes requeridos',
    installFailed: 'No pudimos iniciar la instalación',
    components: {
      dataDir: {
        label: 'Carpeta de datos',
        description: 'Donde se guardan tu base de datos, tus modelos y la caché',
      },
      database: {
        label: 'Base de datos local',
        description: 'Guarda tus tareas, proyectos y contexto',
      },
      ollama: {
        label: 'Motor de IA local',
        description: 'Permite que AI WORKMATE funcione sin enviar tus datos a internet',
      },
      chatModel: {
        label: 'Modelo de conversación',
        description: 'Modelo de lenguaje que responde y propone próximos pasos',
      },
      embeddingModel: {
        label: 'Modelo de búsqueda',
        description: 'Permite encontrar información por significado, no por palabras exactas',
      },
    },
    steps: {
      dataDir: 'Preparando tu carpeta de datos',
      database: 'Creando tu base de datos local',
      ollama: 'Instalando el motor de IA local',
      phi3: 'Descargando el modelo de conversación',
      'nomic-embed': 'Descargando el modelo de búsqueda',
    },
    stepChecking: 'Comprobando los componentes requeridos…',
    stepCheckComplete: 'Comprobación completada',
    stepStarting: 'Iniciando la instalación…',
    stepComplete: 'Instalación completada',
    stepInstallingComponent: 'Instalando los componentes que faltan…',
    stepComponentFailed: 'No pudimos instalar todos los componentes',
    stepDownloadingEngine: 'Descargando el motor de IA local…',
    stepDownloadingModel: 'Descargando los modelos…',
    stepInstallingEngine: 'Instalando el motor de IA local…',
    stepStartingEngine: 'Iniciando el motor de IA local…',
    stepDownloadFailed: 'No pudimos descargar los componentes',
    stepIntegrityFailed: 'Verificamos que el archivo descargado no coincide',
    stepUnverifiedDownload: 'No hay una versión verificada disponible',
    componentFailed: 'No pudimos instalar un componente',
    errorUnverifiedDownload:
      'Por seguridad, solo instalamos el motor de IA cuando la versión publicada está verificada.',
    errorIntegrityFailed: 'El archivo descargado no pasó la verificación de integridad.',
    errorDownloadFailed: 'No pudimos descargar el archivo. Revisa tu conexión a internet.',
    errorModelFailed: 'No pudimos descargar el modelo.',
    alreadyInstalled: 'Todo lo necesario ya está instalado',
    started: 'Instalación iniciada',
    engineInstallStarted: 'Comenzamos a instalar el motor de IA local',
    modelDownloadStarted: 'Comenzamos a descargar el modelo',
    firstRunStarted: 'Comenzamos la instalación inicial',
    setupCompleted: 'Configuración inicial completada',
    checkComplete: 'Comprobación completada',
    noAccountYet: 'Todavía no has conectado ninguna cuenta',
  },

  notifications: {
    saved: 'Guardado',
    removed: 'Eliminado',
    synced: 'Sincronizado',
    syncPending: 'Sincronización pendiente',
    actionNeedsConfirmation: 'AI WORKMATE quiere realizar una acción. Revísala antes de continuar.',
    connectionRestored: 'Conexión restablecida',
    connectionLost: 'Sin conexión con el servidor',
  },

  errors: {
    generic: 'Algo no salió como esperábamos. Inténtalo de nuevo.',
    network: 'No pudimos conectarnos. Revisa tu conexión a internet.',
    notFound: 'No encontramos lo que buscabas.',
    forbidden: 'No tienes permiso para ver esto.',
    server: 'Hay un problema en el servidor. Inténtalo más tarde.',
    timeout: 'La operación tardó demasiado. Inténtalo de nuevo.',
  },

  common: {
    loading: 'Cargando…',
    save: 'Guardar',
    saving: 'Guardando…',
    cancel: 'Cancelar',
    confirm: 'Confirmar',
    close: 'Cerrar',
    back: 'Volver',
    next: 'Siguiente',
    previous: 'Anterior',
    search: 'Buscar',
    filter: 'Filtrar',
    clear: 'Limpiar',
    apply: 'Aplicar',
    yes: 'Sí',
    no: 'No',
    today: 'Hoy',
    tomorrow: 'Mañana',
    yesterday: 'Ayer',
    retry: 'Reintentar',
    seeAll: 'Ver todo',
    empty: 'Nada por aquí todavía',
  },

  privacy: {
    title: 'Privacidad',
    localFirst: 'Tu información se procesa en este equipo.',
    confirmBeforeActing: 'AI WORKMATE te pide confirmación antes de actuar.',
    minimalData: 'Solo guardamos lo indispensable.',
    exportTitle: 'Exportar mis datos',
    deleteTitle: 'Eliminar mis datos',
  },
};