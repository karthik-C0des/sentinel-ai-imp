import { palette as defaultPalette } from '@leafygreen-ui/palette';

const NAVY = {
  dark3: '#0A1226',
  dark2: '#101C3A',
  dark1: '#1A2A42',
  base: '#243B5C',
  light1: '#3D5A82',
  light2: '#C0C5C7',
  light3: '#E8ECEF',
};

const TEAL = {
  dark3: '#004D47',
  dark2: '#007A72',
  dark1: '#009B90',
  base: '#00B5A7',
  light1: '#33C4B8',
  light2: '#99E1DB',
  light3: '#E5F7F6',
};

export const palette = {
  ...defaultPalette,
  green: { ...defaultPalette.green, ...TEAL },
  blue: { ...defaultPalette.blue, ...NAVY },
  gray: { ...defaultPalette.gray, 
    base: '#8797B2',
    light1: '#C0C5C7',
    light2: '#E8ECEF',
    light3: '#F4F7F9'
  }
};
