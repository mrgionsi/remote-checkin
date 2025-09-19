// Centralized fallback data for all components
export const FALLBACK_MUNICIPALITY_OPTIONS = [
  { label: 'ROMA', value: '058091' },
  { label: 'MILANO', value: '015146' },
  { label: 'NAPOLI', value: '063049' },
  { label: 'TORINO', value: '001272' }
];

export const FALLBACK_MUNICIPALITY_MAPPINGS = {
  '058091': 'ROMA',
  '015146': 'MILANO',
  '063049': 'NAPOLI',
  '001272': 'TORINO'
};

export const FALLBACK_DOCUMENT_TYPE_OPTIONS = [
  { label: 'CARTA DI IDENTITA\'', value: 'IDENT' },
  { label: 'PASSAPORTO ORDINARIO', value: 'PASOR' },
  { label: 'PATENTE DI GUIDA', value: 'PATEN' }
];

export const FALLBACK_DOCUMENT_TYPE_MAPPINGS = {
  'IDENT': 'CARTA DI IDENTITA\'',
  'PASOR': 'PASSAPORTO ORDINARIO',
  'PATEN': 'PATENTE DI GUIDA'
};

export const FALLBACK_COUNTRY_OPTIONS = [
  { label: 'ITALIA', value: '100000100' },
  { label: 'STATI UNITI D\'AMERICA', value: '100000536' },
  { label: 'REGNO UNITO', value: '100000219' },
  { label: 'FRANCIA', value: '100000215' }
];

export const FALLBACK_COUNTRY_MAPPINGS = {
  '100000100': 'ITALIA',
  '100000536': 'STATI UNITI D\'AMERICA',
  '100000219': 'REGNO UNITO',
  '100000215': 'FRANCIA'
};
