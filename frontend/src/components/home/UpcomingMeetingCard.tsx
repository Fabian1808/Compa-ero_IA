import { Meeting } from '@/types/api';
import { Card, CardContent } from '@/components/ui';
import { Calendar, Clock, MapPin, Video, ChevronRight } from 'lucide-react';
import { formatDate, formatRelativeTime } from '@/utils/formatters';

interface UpcomingMeetingCardProps {
  meeting: Meeting | null;
}

export function UpcomingMeetingCard({ meeting }: UpcomingMeetingCardProps) {
  if (!meeting) {
    return (
      <Card className="bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700">
        <CardContent className="py-6 text-center">
          <Calendar className="h-10 w-10 text-slate-400 mx-auto mb-2" />
          <p className="text-slate-500 dark:text-slate-400">No hay reuniones próximas</p>
        </CardContent>
      </Card>
    );
  }

  const isSoon = new Date(meeting.start_at) < new Date(Date.now() + 30 * 60 * 1000); // 30 min

  return (
    <Card className={`border-l-4 ${isSoon ? 'border-amber-500' : 'border-slate-200 dark:border-slate-700'}`}>
      <CardContent className="py-4">
        <div className="flex items-start gap-3">
          <div className={`p-2 rounded-lg ${isSoon ? 'bg-amber-100 dark:bg-amber-900/30' : 'bg-slate-100 dark:bg-slate-800'}`}>
            <Calendar className={`h-5 w-5 ${isSoon ? 'text-amber-600 dark:text-amber-400' : 'text-slate-600 dark:text-slate-400'}`} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-medium text-slate-900 dark:text-slate-100 truncate">{meeting.subject}</h3>
              {isSoon && (
                <span className="text-xs font-medium text-amber-700 dark:text-amber-300 bg-amber-100 dark:bg-amber-900 px-1.5 py-0.5 rounded">
                  Pronto
                </span>
              )}
            </div>
            <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400">
              <span className="flex items-center gap-1">
                <Clock className="h-3.5 w-3.5" />
                {formatDate(meeting.start_at)}
              </span>
              {meeting.location && (
                <span className="flex items-center gap-1">
                  <MapPin className="h-3.5 w-3.5" />
                  {meeting.location}
                </span>
              )}
              {meeting.is_online && (
                <span className="flex items-center gap-1">
                  <Video className="h-3.5 w-3.5" />
                  Online
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
              {formatRelativeTime(meeting.start_at)}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}