export interface ProviderConfig {
  id: string;
  name: string;
  logo: string;
  description: string;
  script: string;
  color: string;
  dataTypes?: string[];
  privacyNote?: string;
}

export const providers: Record<string, ProviderConfig> = {
  instagram: {
    id: 'instagram',
    name: 'Instagram',
    logo: 'https://upload.wikimedia.org/wikipedia/commons/a/a5/Instagram_icon.png',
    description: 'Connect your Instagram account to import your profile and posts.',
    script: 'instagram-headless',
    color: '#E4405F',
    dataTypes: ['Profile', 'Posts', 'Followers'],
    privacyNote: 'Your credentials are used once and never stored.'
  },
  icloud_notes: {
    id: 'icloud_notes',
    name: 'iCloud Notes',
    logo: 'https://cdn-icons-png.flaticon.com/512/0/747.png',
    description: 'Connect your iCloud account to import your Apple Notes.',
    script: 'icloud-notes',
    color: '#3693F3',
    dataTypes: ['Notes', 'Folders'],
    privacyNote: 'Your Apple ID credentials are used once for authentication and never stored.'
  }
};
