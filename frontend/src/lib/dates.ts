import dayjs from 'dayjs';
import 'dayjs/locale/ru';

dayjs.locale('ru');

export const fmtTime = (iso: string) => dayjs(iso).format('HH:mm');
export const fmtDateTime = (iso: string) => dayjs(iso).format('D MMMM, HH:mm');
export const weekdayName = (iso: string) => dayjs(iso).format('dddd');
export const toIso = (value: Date) => dayjs(value).format('YYYY-MM-DDTHH:mm:ssZ');
export const toDateOnly = (value: Date) => dayjs(value).format('YYYY-MM-DD');
export const startOfWeek = (value: Date) => dayjs(value).startOf('week').toDate();
export const addDays = (value: Date, days: number) => dayjs(value).add(days, 'day').toDate();

const EVERY_WEEKDAY = [
  'каждое воскресенье',
  'каждый понедельник',
  'каждый вторник',
  'каждую среду',
  'каждый четверг',
  'каждую пятницу',
  'каждую субботу',
];
const ON_WEEKDAYS = ['по воскресеньям', 'по понедельникам', 'по вторникам', 'по средам', 'по четвергам', 'по пятницам', 'по субботам'];

export function describeSeries(series: { first_start: string; duration_minutes: number; interval_weeks: number }): string {
  const day = dayjs(series.first_start).day();
  const when =
    series.interval_weeks === 1 ? EVERY_WEEKDAY[day] : `${ON_WEEKDAYS[day]} раз в ${series.interval_weeks} нед.`;
  return `${when}, ${fmtTime(series.first_start)} (${series.duration_minutes} мин)`;
}
