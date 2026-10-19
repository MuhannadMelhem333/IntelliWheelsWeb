'use client';

import Link from 'next/link';

export interface AppFooterProps {
  theme: 'light' | 'dark';
  language: 'en' | 'ar';
  year: number;
}

export function AppFooter({ theme, language, year }: AppFooterProps) {
  const ar = language === 'ar';
  const links = [
    ['/about', ar ? 'من نحن' : 'About'],
    ['/how-it-works', ar ? 'كيف نعمل' : 'How it works'],
    ['/pricing', ar ? 'الأسعار' : 'Pricing'],
    ['/faq', ar ? 'الأسئلة الشائعة' : 'FAQ'],
    ['/contact', ar ? 'تواصل معنا' : 'Contact'],
  ] as const;

  return <footer className="iw-footer" data-theme={theme}>
    <div><p className="iw-wordmark">IntelliWheels<span>.</span></p><p>{ar ? 'سيارتك القادمة. قرار مدروس.' : 'Your next car. A considered choice.'}</p></div>
    <nav aria-label={ar ? 'معلومات' : 'Information'}>{links.map(([href, label]) => <Link href={href} key={href}>{label}</Link>)}</nav>
    <div className="iw-footer-contact"><span>{ar ? 'عمّان، الأردن' : 'Amman, Jordan'}</span><a href="mailto:intelliwheels03@gmail.com">intelliwheels03@gmail.com</a><a href="tel:+962777381408" dir="ltr">+962 77 738 1408</a></div>
    <div className="iw-footer-bottom"><span>© {year} IntelliWheels</span><Link href="/cookie-policy">{ar ? 'سياسة ملفات تعريف الارتباط' : 'Cookie policy'}</Link><Link href="/disclaimer">{ar ? 'إخلاء المسؤولية' : 'Disclaimer'}</Link><a href="https://www.instagram.com/intelli_wheels1/" target="_blank" rel="noreferrer">Instagram</a></div>
  </footer>;
}
