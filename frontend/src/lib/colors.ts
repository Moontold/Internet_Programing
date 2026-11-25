export interface LessonColor {
  value: string;
  label: string;
}

export const LESSON_COLORS: LessonColor[] = [
  { value: '#cfe6e2', label: 'Бирюзовый' },
  { value: '#a9d5cc', label: 'Полынный' },
  { value: '#cfe7ef', label: 'Небесный' },
  { value: '#d5e3f5', label: 'Голубой' },
  { value: '#b9cfea', label: 'Незабудковый' },
  { value: '#dcdcf0', label: 'Лавандовый' },
  { value: '#c6c8e8', label: 'Барвинковый' },
  { value: '#ecdbef', label: 'Сиреневый' },
  { value: '#e0c4e6', label: 'Орхидея' },
  { value: '#f6d9dd', label: 'Розовый' },
  { value: '#eec0c9', label: 'Пыльная роза' },
  { value: '#f8d5cd', label: 'Коралловый' },
  { value: '#f8e3cf', label: 'Персиковый' },
  { value: '#f0cfae', label: 'Карамельный' },
  { value: '#f1ecc6', label: 'Песочный' },
  { value: '#e6dcaa', label: 'Охра' },
  { value: '#d9e8cd', label: 'Оливковый' },
  { value: '#bfdcaf', label: 'Фисташковый' },
  { value: '#e3e5ea', label: 'Серый' },
  { value: '#ddd6cc', label: 'Кофе с молоком' },
];

export const normalizeColor = (color: string | null) => (color ? color.toLowerCase() : null);

export function mixWithWhite(color: string, amount = 0.55): string {
  const hex = color.replace('#', '');
  if (hex.length !== 6) return color;
  const channels = [0, 2, 4].map((offset) => parseInt(hex.slice(offset, offset + 2), 16));
  if (channels.some((value) => Number.isNaN(value))) return color;
  const mixed = channels.map((value) => Math.round(value + (255 - value) * amount));
  return `#${mixed.map((value) => value.toString(16).padStart(2, '0')).join('')}`;
}
