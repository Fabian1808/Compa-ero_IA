import { useEffect, useState } from 'react';
import { api } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, Badge, Button } from '@/components/ui';
import { Calendar, Clock, MapPin, Video, ChevronLeft, ChevronRight,  Plus } from 'lucide-react';
import { format, parseISO, startOfWeek, endOfWeek, addDays, addWeeks, subWeeks, isSameDay, isToday, isSameMonth } from 'date-fns';
import { es } from 'date-fns/locale';

interface CalendarEvent {
  id: string;
  subject: string;
  start_at: string;
  end_at: string;
  location: string | null;
  is_online: boolean;
  meeting_url: string | null;
  attendees: string;
  time_until?: string;
}

export function CalendarPage() {
  const [currentWeek, setCurrentWeek] = useState<Date>(startOfWeek(new Date(), { weekStartsOn: 1 }));
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState<'week' | 'day' | 'month'>('week');

  const weekStart = startOfWeek(currentWeek, { weekStartsOn: 1 });
  const weekEnd = endOfWeek(currentWeek, { weekStartsOn: 1 });

  useEffect(() => {
    fetchEvents();
  }, [currentWeek]);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const start = weekStart.toISOString();
      const end = weekEnd.toISOString();
      const response = await api.get(`/calendar/events?start=${start}&end=${end}`);
      setEvents(response.data.events || []);
    } catch (err) {
      console.error('Failed to fetch events:', err);
    } finally {
      setLoading(false);
    }
  };

  const getEventsForDay = (date: Date) => {
    return events.filter(e => isSameDay(parseISO(e.start_at), date));
  };

  const goToToday = () => {
    setCurrentWeek(new Date());
  };

  const prevWeek = () => setCurrentWeek(subWeeks(currentWeek, 1));
  const nextWeek = () => setCurrentWeek(addWeeks(currentWeek, 1));

  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Calendario</h1>
          <p className="text-slate-500 dark:text-slate-400">
            {format(weekStart, 'd MMM', { locale: es })} - {format(weekEnd, 'd MMM yyyy', { locale: es })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={prevWeek}><ChevronLeft className="h-4 w-4" /></Button>
          <Button variant="secondary" onClick={nextWeek}><ChevronRight className="h-4 w-4" /></Button>
          <Button variant="secondary" onClick={goToToday}><Calendar className="h-4 w-4" /> Hoy</Button>
          <Button><Plus className="h-4 w-4" /> Nuevo evento</Button>
        </div>
      </div>

      {/* Week View */}
      <div className="grid grid-cols-7 gap-1">
        {days.map((day) => (
          <DayColumn key={day.toISOString()} day={day} events={getEventsForDay(day)} />
        ))}
      </div>

      {/* Upcoming Events List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            Próximos eventos
            <Badge variant="primary">{events.length} esta semana</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
            </div>
          ) : events.length === 0 ? (
            <div className="text-center py-8 text-slate-500 dark:text-slate-400">
              <Calendar className="h-12 w-12 mx-auto mb-3 text-slate-300 dark:text-slate-600" />
              <p>No hay eventos esta semana</p>
            </div>
          ) : (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {events
                .sort((a, b) => new Date(a.start_at).getTime() - new Date(b.start_at).getTime())
                .slice(0, 20)
                .map((event) => (
                  <EventCard key={event.id} event={event} />
                ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function DayColumn({ day, events }: { day: Date; events: CalendarEvent[] }) {
  const isTodayDay = isToday(day);
  const isCurrentMonth = isSameMonth(day, new Date());

  return (
    <div className={`flex flex-col min-h-[120px] p-2 rounded-lg transition-colors ${
      isTodayDay 
        ? 'bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800' 
        : 'bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-700/50'
    }`}>
      <div className={`text-center mb-2 ${isTodayDay ? 'text-primary-700 dark:text-primary-300 font-bold' : 'text-slate-600 dark:text-slate-400'}`}>
        {format(day, 'EEE', { locale: es })}
      </div>
      <div className={`text-2xl font-medium text-center ${isTodayDay ? 'text-primary-700 dark:text-primary-300' : 'text-slate-900 dark:text-slate-100'}`}>
        {format(day, 'd')}
      </div>
      <div className="flex-1 overflow-y-auto space-y-1 mt-2">
        {events.slice(0, 4).map((event) => (
          <MiniEventCard key={event.id} event={event} />
        ))}
        {events.length > 4 && (
          <div className="text-center text-xs text-slate-500 dark:text-slate-400 mt-1">
            +{events.length - 4} más
          </div>
        )}
      </div>
    </div>
  );
}

function MiniEventCard({ event }: { event: CalendarEvent }) {
  const start = parseISO(event.start_at);
  return (
    <div className="bg-primary-100 dark:bg-primary-900/30 text-primary-800 dark:text-primary-200 text-xs px-2 py-1 rounded truncate cursor-pointer hover:bg-primary-200 dark:hover:bg-primary-800/30 transition-colors">
      <div className="font-medium truncate">{event.subject}</div>
      <div className="flex items-center gap-1 opacity-80">
        <Clock className="h-2.5 w-2.5" />
        {format(start, 'HH:mm')}
      </div>
    </div>
  );
}

function EventCard({ event }: { event: CalendarEvent }) {
  const start = parseISO(event.start_at);
  const end = parseISO(event.end_at);
  const isOnline = event.is_online;

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors border border-slate-200 dark:border-slate-700">
      <div className="flex-shrink-0 w-14 text-center">
        <div className="text-2xl font-bold text-primary-700 dark:text-primary-300">{format(start, 'd')}</div>
        <div className="text-xs text-slate-500 dark:text-slate-400 uppercase">{format(start, 'MMM', { locale: es })}</div>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="font-medium text-slate-900 dark:text-slate-100 truncate">{event.subject}</h4>
          {isOnline && <Badge variant="primary"><Video className="h-3 w-3" /> Online</Badge>}
        </div>
        <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
          <span className="flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" />
            {format(start, 'HH:mm')} - {format(end, 'HH:mm')}
          </span>
          {event.location && (
            <span className="flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" />
              {event.location}
            </span>
          )}
        </div>
        {event.time_until && (
          <div className="text-xs text-primary-600 dark:text-primary-400 mt-1">{event.time_until}</div>
        )}
      </div>
    </div>
  );
}