'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState, type FormEvent } from 'react';
import { fetchCars } from '@/lib/api';
import type { Car } from '@/lib/types';
import { useAuth } from '@/context/AuthContext';
import { usePublicPreferences } from '@/components/public/PublicRouteShell';

const DEFAULT_FILTERS = { make: 'all', search: '', sort: 'default' as const, category: 'all' as const };

export function PublicHomeView() {
  const router = useRouter();
  const { token, formatPrice, user } = useAuth();
  const { language } = usePublicPreferences();
  const [cars, setCars] = useState<Car[]>([]);
  const [error, setError] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [search, setSearch] = useState('');
  const ar = language === 'ar';

  useEffect(() => {
    let live = true;
    fetchCars(DEFAULT_FILTERS, undefined, token).then((response) => {
      if (live) { setCars((response.cars ?? []).slice(0, 4)); setError(false); }
    }).catch(() => { if (live) setError(true); })
      .finally(() => { if (live) setLoaded(true); });
    return () => { live = false; };
  }, [token]);

  const submitSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const params = new URLSearchParams();
    if (search.trim()) params.set('search', search.trim());
    router.push('/listings' + (params.size ? '?' + params : ''));
  };

  return <main className="iw-home">
    <section className="iw-hero">
      <div>
        <p className="iw-eyebrow">{ar ? 'إنتلي ويلز / سوق السيارات' : 'INTELLIWHEELS / THE MOTOR MARKETPLACE'}</p>
        <h1>{ar ? 'سيارتك القادمة.' : 'Your next car.'}<br/><span>{ar ? 'قرار مدروس.' : 'A considered choice.'}</span></h1>
        <p className="iw-hero-copy">{ar ? 'تصفح السيارات، قارن الخيارات، وتواصل مع البائع مباشرة. كل ما تحتاجه لخطوتك القادمة، في مكان واحد.' : 'Explore the cars. Compare the possibilities. Connect directly with sellers. Everything for your next move, in one place.'}</p>
        <Link href="/dealers" className="iw-text-link">{ar ? 'تعرف على الوكلاء' : 'Explore our dealer directory'} ↗</Link>
      </div>
      <form onSubmit={submitSearch} className="iw-search-panel">
        <p className="iw-eyebrow">{ar ? 'ابدأ رحلتك' : 'START YOUR SEARCH'}</p>
        <h2>{ar ? 'ما الذي تبحث عنه؟' : 'What moves you?'}</h2>
        <label htmlFor="home-car-search">{ar ? 'الماركة أو الموديل' : 'Make or model'}</label>
        <input id="home-car-search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder={ar ? 'مثال: BMW أو كامري' : 'Try BMW or Camry'} maxLength={100}/>
        <button className="iw-primary" type="submit">{ar ? 'تصفح السيارات' : 'Explore vehicles'} <span aria-hidden="true">↗</span></button>
        <p>{ar ? 'تبحث عن شيء محدد؟ استخدم الفلاتر في صفحة السيارات.' : 'Something specific in mind? Refine your search with our listing filters.'}</p>
      </form>
    </section>
    <section className="iw-service-strip" aria-label={ar ? 'خدماتنا' : 'Explore IntelliWheels'}>
      {[
        { href: '/listings', title: ar ? 'اعثر على سيارتك' : 'Find your car', detail: ar ? 'تصفح وقارن بثقة' : 'Browse. Compare. Decide.' },
        { href: user ? '/my-listings/new' : '/account', title: ar ? 'اعرض سيارتك' : 'Sell your car', detail: ar ? 'أوصل إعلانك إلى المشترين' : 'Make your next move.' },
        { href: '/assistant', title: ar ? 'تحتاج إلى مساعدة؟' : 'Need a second opinion?', detail: ar ? 'اسأل مساعد السيارات' : 'Talk to the vehicle assistant.' },
      ].map((item, index) => <Link href={item.href} key={item.href}><span className="iw-step">0{index + 1}</span><div><h2>{item.title}</h2><p>{item.detail}</p></div><span aria-hidden="true">↗</span></Link>)}
    </section>
    <section className="iw-inventory">
      <div className="iw-section-heading"><div><p className="iw-eyebrow">{ar ? 'اكتشف الخيارات' : 'EXPLORE THE POSSIBILITIES'}</p><h2>{ar ? 'في السوق الآن' : 'On the market.'}</h2></div><Link href="/listings" className="iw-text-link">{ar ? 'عرض جميع السيارات' : 'View all vehicles'} ↗</Link></div>
      {!loaded ? <p className="iw-empty" role="status">{ar ? 'جارٍ تحميل السيارات…' : 'Loading vehicles…'}</p> : error ? <p className="iw-empty" role="alert">{ar ? 'تعذر تحميل السيارات. يرجى المحاولة مجدداً.' : 'Vehicles could not be loaded. Please try again.'} <Link href="/listings" className="iw-text-link">{ar ? 'فتح السيارات' : 'Open listings'}</Link></p> : cars.length === 0 ? <p className="iw-empty">{ar ? 'لا توجد سيارات معروضة حالياً.' : 'No vehicles are listed at the moment.'}</p> : null}
      <div className="iw-car-grid">{cars.map((car) => <Link href={'/cars/' + car.id + '?from=home'} key={car.id} className="iw-car-card"><Image unoptimized src={car.imageUrls?.[0] || car.galleryImages?.[0] || car.image || '/placeholder-car.svg'} alt={car.make + ' ' + car.model} width={480} height={320} className="iw-car-image"/><div><p className="iw-eyebrow">{car.year} / {car.make}</p><h3>{car.model}</h3><p className="iw-car-price">{formatPrice(car.price, car.currency)}</p><span className="iw-car-detail">{ar ? 'عرض التفاصيل' : 'View details'} ↗</span></div></Link>)}</div>
    </section>
    <section className="iw-sell-panel"><div><p className="iw-eyebrow">{ar ? 'جاهز للتغيير؟' : 'READY FOR SOMETHING NEW?'}</p><h2>{ar ? 'رحلتك القادمة تبدأ هنا.' : 'Your next chapter starts here.'}</h2><p>{ar ? 'أضف الصور والتفاصيل، واعرض سيارتك للمشترين.' : 'Add the photographs and details. Put your car in front of its next owner.'}</p></div><Link href={user ? '/my-listings/new' : '/account'} className="iw-primary">{ar ? 'اعرض سيارتك' : 'Create a listing'}</Link></section>
  </main>;
}
