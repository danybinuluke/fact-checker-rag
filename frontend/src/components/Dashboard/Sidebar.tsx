import React from 'react';
import type { TabType } from '@/app/page';
import StaggeredMenu from './StaggeredMenu';

interface SidebarProps {
  activeTab: TabType;
  onTabChange: (tab: TabType) => void;
}

export function Sidebar({ activeTab, onTabChange }: SidebarProps) {
  const menuItems = [
    { 
      id: 'verify',
      label: 'Verify Claims', 
      ariaLabel: 'Verify Claims', 
      onClick: () => onTabChange('verify')
    },
    { 
      id: 'metrics',
      label: 'System Metrics', 
      ariaLabel: 'System Metrics', 
      onClick: () => onTabChange('metrics')
    },
  ];

  const socialItems = [
    { label: 'GitHub', link: 'https://github.com' },
  ];

  return (
    <StaggeredMenu
      position="left"
      isFixed={true}
      items={menuItems}
      socialItems={socialItems}
      displaySocials={true}
      displayItemNumbering={true}
      menuButtonColor="#fff"
      openMenuButtonColor="#fff"
      changeMenuColorOnOpen={true}
      colors={['#1a1a2e', '#16213e', '#0f3460']}
      logoUrl="" // Removing logo so it just shows the hamburger text
      accentColor="#3b82f6"
    />
  );
}
