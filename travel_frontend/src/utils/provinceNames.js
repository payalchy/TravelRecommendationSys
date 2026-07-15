const provinceNameMap = {
  '1': 'Koshi',
  '2': 'Madhesh',
  '3': 'Bagmati',
  '4': 'Gandaki',
  '5': 'Lumbini',
  '6': 'Karnali',
  '7': 'Sudurpaschim',
};

export function formatProvinceName(value) {
  if (value == null) return '';

  const text = String(value).trim();
  if (!text) return '';

  return provinceNameMap[text] || text;
}
