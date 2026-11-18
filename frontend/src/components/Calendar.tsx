import type { DatesSetArg, EventClickArg, EventContentArg, EventDropArg, EventMountArg } from '@fullcalendar/core';
import ruLocale from '@fullcalendar/core/locales/ru';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin, { type DateClickArg } from '@fullcalendar/interaction';
import FullCalendar from '@fullcalendar/react';
import timeGridPlugin from '@fullcalendar/timegrid';

import type { LessonShort } from '../api/types';

interface Props {
  lessons: LessonShort[];
  onRangeChange: (start: Date, end: Date) => void;
  onOpen: (lessonId: number) => void;
  onMove: (lesson: LessonShort, newStart: Date, revert: () => void) => void;
  onCreate: (start: Date) => void;
  onContextMenu: (lesson: LessonShort, x: number, y: number) => void;
}

const EVENT_COLORS: Record<LessonShort['status'], string> = {
  planned: '#cfe6e2',
  held: '#e9ebf0',
  cancelled: '#f5f6f8',
};

const eventEnd = (lesson: LessonShort) =>
  new Date(new Date(lesson.scheduled_start).getTime() + lesson.duration_minutes * 60000).toISOString();

export function Calendar({ lessons, onRangeChange, onOpen, onMove, onCreate, onContextMenu }: Props) {
  const shown = lessons.filter((item) => item.status !== 'cancelled');
  const byId = new Map(shown.map((item) => [String(item.id), item]));
  const events = shown.map((lesson) => ({
    id: String(lesson.id),
    title: [lesson.title, lesson.topic].filter(Boolean).join(' · '),
    start: lesson.scheduled_start,
    end: eventEnd(lesson),
    backgroundColor: EVENT_COLORS[lesson.status],
    borderColor: EVENT_COLORS[lesson.status],
    editable: lesson.status === 'planned',
  }));

  const renderEvent = (arg: EventContentArg) => {
    const names = (byId.get(arg.event.id)?.participants ?? []).map((item) => item.full_name).join(', ');
    return (
      <div className="fc-lesson">
        <div className="fc-lesson__time">{arg.timeText}</div>
        {arg.event.title && <div className="fc-lesson__title">{arg.event.title}</div>}
        {names && <div className="fc-lesson__names">{names}</div>}
      </div>
    );
  };

  return (
    <FullCalendar
      plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
      locale={ruLocale}
      initialView="timeGridWeek"
      headerToolbar={{ left: 'prev,next today', center: 'title', right: 'timeGridWeek,dayGridMonth' }}
      firstDay={1}
      slotMinTime="08:00:00"
      slotMaxTime="23:00:00"
      allDaySlot={false}
      height="auto"
      nowIndicator
      events={events}
      editable
      eventDurationEditable={false}
      eventLongPressDelay={300}
      longPressDelay={300}
      eventContent={renderEvent}
      eventTimeFormat={{ hour: '2-digit', minute: '2-digit', hour12: false }}
      slotLabelFormat={{ hour: '2-digit', minute: '2-digit', hour12: false }}
      defaultRangeSeparator=" – "
      datesSet={(arg: DatesSetArg) => onRangeChange(arg.start, arg.end)}
      eventClick={(arg: EventClickArg) => onOpen(Number(arg.event.id))}
      eventDrop={(arg: EventDropArg) => {
        const lesson = byId.get(arg.event.id);
        if (!lesson || !arg.event.start) {
          arg.revert();
          return;
        }
        onMove(lesson, arg.event.start, arg.revert);
      }}
      dateClick={(arg: DateClickArg) => onCreate(arg.date)}
      eventDidMount={(arg: EventMountArg) => {
        arg.el.addEventListener('contextmenu', (event: MouseEvent) => {
          event.preventDefault();
          const lesson = byId.get(arg.event.id);
          if (lesson) onContextMenu(lesson, event.clientX, event.clientY);
        });
      }}
    />
  );
}
