'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useRef, type ReactNode } from 'react';

interface PublicHeaderProps {
  theme: 'light' | 'dark';
  language: 'en' | 'ar';
  pathname: string;
  links: ReadonlyArray<{ href: string; label: string }>;
  preferences: ReactNode;
  mobileOpen: boolean;
  onToggleMenu: () => void;
  onNavigate: () => void;
}

/** Presentation only: preference, session, and unread state belong to the shell. */
export function PublicHeader({ theme, language, pathname, links, preferences, mobileOpen, onToggleMenu, onNavigate }: PublicHeaderProps) {
  const menuButton = useRef<HTMLButtonElement>(null);
  return (
        <header className="iw-header" onKeyDown={(event) => {
          if (event.key === 'Escape' && mobileOpen) {
            event.preventDefault();
            onNavigate();
            menuButton.current?.focus();
          }
        }}>
          <div className="iw-header-top">
            <Link href="/" className="iw-logo" aria-label={language === 'ar' ? 'إنتلي ويلز — الرئيسية' : 'IntelliWheels — Home'} style={{ position: 'relative', display: 'block', maxWidth: 220, height: 54, overflow: 'hidden', flexShrink: 0 }}>
              <Image src={theme === 'dark' ? '/IntelliWheels_Logo_Dark.png' : '/IntelliWheels_Logo_Light.png'} alt="IntelliWheels" width={220} height={220} sizes="220px" style={{ position: 'absolute', width: '100%', maxWidth: 220, height: 'auto', top: '50%', transform: 'translateY(-46%)' }} priority />
            </Link>
            <div className="iw-desktop-preferences">{preferences}</div>
            <Link href="/my-listings/new" className="iw-primary iw-sell-link">{language === 'ar' ? 'بيع سيارتك' : 'Sell your car'}</Link>
            <button ref={menuButton} type="button" className="iw-menu-toggle" aria-expanded={mobileOpen} aria-controls="public-mobile-navigation" aria-label={language === 'ar' ? (mobileOpen ? 'إغلاق قائمة التنقل' : 'فتح قائمة التنقل') : (mobileOpen ? 'Close navigation' : 'Open navigation')} onClick={onToggleMenu}>
              {mobileOpen ? '✕' : '☰'}
            </button>
          </div>
          <nav className="iw-desktop-nav" aria-label={language === 'ar' ? 'التنقل الرئيسي' : 'Public navigation'}>
            {links.map((link) => <Link key={link.href} href={link.href} aria-current={pathname === link.href ? 'page' : undefined}>{link.label}</Link>)}
          </nav>
          {mobileOpen ? (
            <nav id="public-mobile-navigation" className="iw-mobile-nav" aria-label={language === 'ar' ? 'التنقل على الجوال' : 'Mobile navigation'}>
              {links.map((link) => <Link key={link.href} href={link.href} aria-current={pathname === link.href ? 'page' : undefined} onClick={onNavigate}>{link.label}</Link>)}
              {preferences}
            </nav>
          ) : null}
        </header>
  );
}
