// ISO 3166-1 alpha-2 codes — must match backend services/locations.py
// Sorted by region, then alphabetically.

export const COUNTRIES = [
  // North America
  { code: 'US', label: 'United States' },
  { code: 'CA', label: 'Canada' },
  { code: 'MX', label: 'Mexico' },

  // Oceania
  { code: 'AU', label: 'Australia' },
  { code: 'NZ', label: 'New Zealand' },

  // UK & Ireland
  { code: 'GB', label: 'United Kingdom' },
  { code: 'IE', label: 'Ireland' },

  // Europe — West
  { code: 'IT', label: 'Italy' },
  { code: 'ES', label: 'Spain' },
  { code: 'FR', label: 'France' },
  { code: 'DE', label: 'Germany' },
  { code: 'PT', label: 'Portugal' },
  { code: 'NL', label: 'Netherlands' },
  { code: 'BE', label: 'Belgium' },
  { code: 'CH', label: 'Switzerland' },
  { code: 'AT', label: 'Austria' },

  // Europe — North
  { code: 'SE', label: 'Sweden' },
  { code: 'NO', label: 'Norway' },
  { code: 'DK', label: 'Denmark' },
  { code: 'FI', label: 'Finland' },

  // Europe — East
  { code: 'PL', label: 'Poland' },
  { code: 'CZ', label: 'Czech Republic' },
  { code: 'RO', label: 'Romania' },
  { code: 'GR', label: 'Greece' },
  { code: 'TR', label: 'Türkiye' },
  { code: 'RU', label: 'Russia' },
  { code: 'UA', label: 'Ukraine' },

  // LATAM
  { code: 'BR', label: 'Brazil' },
  { code: 'AR', label: 'Argentina' },
  { code: 'CL', label: 'Chile' },
  { code: 'CO', label: 'Colombia' },
  { code: 'PE', label: 'Peru' },

  // Asia
  { code: 'JP', label: 'Japan' },
  { code: 'KR', label: 'South Korea' },
  { code: 'CN', label: 'China' },
  { code: 'HK', label: 'Hong Kong' },
  { code: 'TW', label: 'Taiwan' },
  { code: 'IN', label: 'India' },
  { code: 'ID', label: 'Indonesia' },
  { code: 'TH', label: 'Thailand' },
  { code: 'VN', label: 'Vietnam' },
  { code: 'MY', label: 'Malaysia' },
  { code: 'PH', label: 'Philippines' },
  { code: 'SG', label: 'Singapore' },

  // MENA + Africa
  { code: 'AE', label: 'United Arab Emirates' },
  { code: 'SA', label: 'Saudi Arabia' },
  { code: 'IL', label: 'Israel' },
  { code: 'EG', label: 'Egypt' },
  { code: 'ZA', label: 'South Africa' },
];

export const COUNTRY_OPTIONS = COUNTRIES.map((c) => ({
  value: c.code,
  label: `${c.code} — ${c.label}`,
}));

export const countryLabel = (code) => {
  const c = COUNTRIES.find((x) => x.code === code);
  return c ? c.label : code;
};
