'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState, type FormEvent } from 'react';
import { analyzeListingImage, createListing, fetchCarById, fetchEngines, fetchMakes, fetchModels, getPriceEstimate, updateListing, uploadListingImage, uploadListingVideo } from '@/lib/api';
import type { Car, CurrencyCode, FuelType, PaymentType, RegionalSpec, TransmissionType, VehicleCategory, VehicleCondition, VisionAttributes } from '@/lib/types';
import { useAuth } from '@/context/AuthContext';
import { usePublicPreferences } from '@/components/public/PublicRouteShell';
import { RouteErrorState } from '@/components/RouteErrorState';
import { listingMediaPayload } from '@/lib/listingMediaPayload';
import { addRecoveredMedia, addUploadedMedia } from '@/lib/recoveredListingMedia';
import { uploadListingBatch } from '@/lib/listingUploadBatch';
import { getCookieSessionRevision } from '@/lib/cookieSession';
import { UploadRecovery } from './UploadRecovery';

interface ListingEditorViewProps { listingId?: string; }
interface ListingFormState {
  assetIds: Record<string, string>;
  make: string; model: string; year: string; price: string; currency: CurrencyCode; bodyStyle: string; horsepower: string;
  engine: string; fuelEconomy: string; odometer: string; image: string; galleryImages: string[]; videoUrls: string[];
  description: string; category: VehicleCategory; condition: VehicleCondition; exteriorColor: string; interiorColor: string;
  transmission: TransmissionType | ''; fuelType: FuelType | ''; regionalSpec: RegionalSpec | ''; paymentType: PaymentType;
  city: string; neighborhood: string; trim: string;
}

const EMPTY_FORM: ListingFormState = {
  assetIds: {},
  make: '', model: '', year: '', price: '', currency: 'JOD', bodyStyle: '', horsepower: '', engine: '', fuelEconomy: '',
  odometer: '', image: '', galleryImages: [], videoUrls: [], description: '', category: 'car', condition: 'used',
  exteriorColor: '', interiorColor: '', transmission: '', fuelType: '', regionalSpec: '', paymentType: 'cash', city: '', neighborhood: '', trim: '',
};
const CURRENCIES: CurrencyCode[] = ['JOD', 'AED', 'USD', 'EUR', 'GBP', 'SAR', 'QAR', 'BHD', 'KWD', 'OMR'];
const CATEGORIES: Array<[VehicleCategory, string]> = [['car', 'Car'], ['suv', 'SUV'], ['truck', 'Truck'], ['bike', 'Motorcycle'], ['van', 'Van'], ['bus', 'Bus'], ['other', 'Other']];
const CONDITIONS: Array<[VehicleCondition, string]> = [['new', 'New'], ['used', 'Used'], ['certified', 'Certified pre-owned']];
const TRANSMISSIONS: Array<[TransmissionType | '', string]> = [['', 'Select transmission'], ['automatic', 'Automatic'], ['manual', 'Manual'], ['cvt', 'CVT'], ['other', 'Other']];
const FUELS: Array<[FuelType | '', string]> = [['', 'Select fuel type'], ['petrol', 'Petrol'], ['diesel', 'Diesel'], ['electric', 'Electric'], ['hybrid', 'Hybrid'], ['plugin_hybrid', 'Plug-in hybrid'], ['lpg', 'LPG'], ['other', 'Other']];
const REGIONAL_SPECS: Array<[RegionalSpec | '', string]> = [['', 'Select regional specification'], ['gcc', 'GCC'], ['american', 'American'], ['european', 'European'], ['japanese', 'Japanese'], ['korean', 'Korean'], ['other', 'Other']];
const PAYMENTS: Array<[PaymentType, string]> = [['cash', 'Cash only'], ['installments', 'Installments only'], ['both', 'Cash or installments']];

function formFromCar(car: Car): ListingFormState {
  const mediaImages = car.mediaGallery?.filter((item) => item.type === 'image').map((item) => item.url) ?? [];
  const mediaVideos = car.mediaGallery?.filter((item) => item.type === 'video').map((item) => item.url) ?? [];
  const galleryImages = [...new Set([...(car.galleryImages ?? []), ...mediaImages])];
  const videoUrls = [...new Set([...(car.videoUrl ? [car.videoUrl] : []), ...mediaVideos])];
  return {
    assetIds: Object.fromEntries((car.mediaGallery ?? []).filter((item) => item.assetId).map((item) => [item.url, item.assetId as string])),
    make: car.make ?? '', model: car.model ?? '', year: car.year?.toString() ?? '', price: car.price?.toString() ?? '', currency: car.currency ?? 'JOD',
    bodyStyle: car.specs?.bodyStyle ?? '', horsepower: car.specs?.horsepower?.toString() ?? '', engine: car.specs?.engine ?? '', fuelEconomy: car.specs?.fuelEconomy ?? '',
    odometer: car.odometerKm?.toString() ?? '', image: car.image ?? galleryImages[0] ?? '', galleryImages, videoUrls, description: car.description ?? '',
    category: car.category ?? 'car', condition: car.condition ?? 'used', exteriorColor: car.exteriorColor ?? '', interiorColor: car.interiorColor ?? '',
    transmission: car.transmission ?? '', fuelType: car.fuelType ?? '', regionalSpec: car.regionalSpec ?? '', paymentType: car.paymentType ?? 'cash',
    city: car.city ?? '', neighborhood: car.neighborhood ?? '', trim: car.trim ?? '',
  };
}

function toPayload(form: ListingFormState): Partial<Car> {
  return {
    make: form.make.trim(), model: form.model.trim(), year: Number(form.year), price: Number(form.price), currency: form.currency,
    odometerKm: form.odometer ? Number(form.odometer) : undefined, ...listingMediaPayload(form),
    description: form.description, specs: { bodyStyle: form.bodyStyle, horsepower: form.horsepower ? Number(form.horsepower) : undefined, engine: form.engine, fuelEconomy: form.fuelEconomy },
    category: form.category, condition: form.condition, exteriorColor: form.exteriorColor || undefined, interiorColor: form.interiorColor || undefined,
    transmission: form.transmission || undefined, fuelType: form.fuelType || undefined, regionalSpec: form.regionalSpec || undefined,
    paymentType: form.paymentType, city: form.city || undefined, neighborhood: form.neighborhood || undefined, trim: form.trim || undefined,
  };
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '');
    reader.onerror = () => reject(new Error('Unable to read the selected image'));
    reader.readAsDataURL(file);
  });
}

export function ListingEditorView({ listingId }: ListingEditorViewProps) {
  const router = useRouter();
  const { token, loading: authLoading, sessionValidated } = useAuth();
  const { theme, language } = usePublicPreferences();
  const [form, setForm] = useState<ListingFormState>(EMPTY_FORM);
  const [makes, setMakes] = useState<string[]>([]); const [models, setModels] = useState<string[]>([]); const [engines, setEngines] = useState<string[]>([]);
  const [loading, setLoading] = useState(Boolean(listingId)); const [submitting, setSubmitting] = useState(false); const [uploading, setUploading] = useState(false);
  const [assisting, setAssisting] = useState(false); const [error, setError] = useState(''); const [notice, setNotice] = useState('');
  const [vision, setVision] = useState<VisionAttributes | null>(null);
  const uploadLock = useRef(false);
  const uploadEpoch = useRef(0);
  useEffect(() => () => { uploadEpoch.current++; }, [token, sessionValidated, listingId]);
  const dark = theme === 'dark'; const numericId = listingId ? Number(listingId) : null;
  const fieldClass = `w-full rounded-xl border p-3 ${dark ? 'border-slate-600 bg-slate-800 text-white' : 'border-slate-200 bg-white text-slate-900'}`;

  useEffect(() => {
    if (!token || !sessionValidated) return;
    let live = true; fetchMakes(token).then((response) => { if (live) setMakes(response.makes ?? []); }).catch(() => undefined);
    return () => { live = false; };
  }, [sessionValidated, token]);
  useEffect(() => {
    if (!token || !sessionValidated || !listingId) return;
    if (!Number.isInteger(numericId) || (numericId ?? 0) <= 0) { setError('Invalid listing ID.'); setLoading(false); return; }
    let live = true;
    fetchCarById(numericId as number, token).then((response) => { if (live && response.car) setForm(formFromCar(response.car)); })
      .catch((loadError: unknown) => { if (live) setError(loadError instanceof Error ? loadError.message : 'Unable to load this listing'); })
      .finally(() => { if (live) setLoading(false); });
    return () => { live = false; };
  }, [listingId, numericId, sessionValidated, token]);
  useEffect(() => {
    if (!form.make || !token) { setModels([]); return; }
    let live = true; fetchModels(form.make, token).then((response) => { if (live) setModels(response.models ?? []); }).catch(() => undefined);
    return () => { live = false; };
  }, [form.make, token]);
  useEffect(() => {
    if (!form.make || !form.model || !token) { setEngines([]); return; }
    let live = true; fetchEngines(form.make, form.model, token).then((response) => { if (live) setEngines(response.engines ?? []); }).catch(() => undefined);
    return () => { live = false; };
  }, [form.make, form.model, token]);

  const update = <K extends keyof ListingFormState>(field: K, value: ListingFormState[K]) => setForm((current) => ({ ...current, [field]: value }));
  const uploadMedia = async (files: FileList | null, kind: 'image' | 'video') => {
    if (!files || !token || !sessionValidated || uploadLock.current || submitting) return;
    const limit = kind === 'image' ? 12 : 2;
    const count = kind === 'image' ? new Set([form.image, ...form.galleryImages].filter(Boolean)).size : form.videoUrls.length;
    const selected = Array.from(files).slice(0, Math.max(0, limit - count));
    if (!selected.length) { setNotice(language === 'ar' ? 'وصلت إلى الحد الأقصى للملفات.' : 'Media limit reached.'); return; }
    uploadLock.current = true;
    const epoch = uploadEpoch.current;
    const sessionRevision = getCookieSessionRevision();
    setUploading(true); setError(''); setNotice('');
    try {
      const upload = kind === 'image' ? uploadListingImage : uploadListingVideo;
      const { uploads, failed } = await uploadListingBatch(selected, (file) => upload(file, token));
      if (epoch !== uploadEpoch.current || sessionRevision !== getCookieSessionRevision()) return;
      setForm((current) => uploads.reduce((draft, item) => addUploadedMedia(draft, kind, item.url, item.assetId), current));
      if (failed) setError(language === 'ar'
        ? `تعذر رفع ${failed} من الملفات. احتُفظ بالملفات الناجحة في المسودة. لا تعِد رفعها.`
        : `${failed} upload(s) failed. Successful files were kept in the draft; do not upload them again.`);
      if (files.length > selected.length) setNotice(language === 'ar' ? 'لم تُرفع الملفات التي تتجاوز الحد المسموح.' : 'Files exceeding the media limit were not uploaded.');
    } finally { uploadLock.current = false; setUploading(false); }
  };
  const uploadImages = (files: FileList | null) => uploadMedia(files, 'image');
  const uploadVideos = (files: FileList | null) => uploadMedia(files, 'video');
  const estimatePrice = async () => {
    if (!token || !form.make || !form.model || !form.year) { setNotice('Add make, model, and year first.'); return; }
    setAssisting(true); setError('');
    try {
      const response = await getPriceEstimate({ make: form.make, model: form.model, year: Number(form.year), bodyStyle: form.bodyStyle || undefined, horsepower: form.horsepower ? Number(form.horsepower) : undefined, currency: form.currency }, token);
      update('price', String(Math.round(response.estimate))); setNotice(`Suggested price: ${response.currency} ${Math.round(response.estimate).toLocaleString()}`);
    } catch (assistError: unknown) { setError(assistError instanceof Error ? assistError.message : 'Unable to estimate the price'); }
    finally { setAssisting(false); }
  };
  const analyzeImage = async (file: File | undefined) => {
    if (!file || !token) return;
    setAssisting(true); setError('');
    try {
      const response = await analyzeListingImage({ image_base64: await fileToBase64(file), mime_type: file.type }, token); const attributes = response.attributes;
      setVision(attributes); setForm((current) => ({ ...current, make: attributes.make ?? current.make, model: attributes.model ?? current.model,
        year: attributes.year ? String(attributes.year) : current.year, bodyStyle: attributes.bodyStyle ?? current.bodyStyle,
        exteriorColor: attributes.color ?? current.exteriorColor, description: attributes.conditionDescription ?? current.description,
        price: attributes.estimatedPrice ? String(Math.round(attributes.estimatedPrice)) : current.price, currency: attributes.currency ?? current.currency }));
    } catch (assistError: unknown) { setError(assistError instanceof Error ? assistError.message : 'Unable to analyze the image'); }
    finally { setAssisting(false); }
  };
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); if (!token) return;
    const year = Number(form.year); const price = Number(form.price);
    if (!form.make.trim() || !form.model.trim() || !form.year || !form.price) { setError('Make, model, year, and price are required.'); return; }
    if (!Number.isFinite(year) || year < 1900 || year > new Date().getFullYear() + 2) { setError(`Year must be between 1900 and ${new Date().getFullYear() + 2}.`); return; }
    if (!Number.isFinite(price) || price < 0) { setError('Price must be a valid positive number.'); return; }
    setSubmitting(true); setError('');
    try {
      const response = listingId ? await updateListing(numericId as number, toPayload(form), token) : await createListing(toPayload(form), token);
      if (response.success === false) throw new Error(typeof response.error === 'string' ? response.error : 'Unable to save the listing');
      router.push('/my-listings'); router.refresh();
    } catch (saveError: unknown) { setError(saveError instanceof Error ? saveError.message : 'Unable to save the listing'); }
    finally { setSubmitting(false); }
  };

  if (authLoading) return <main className="p-8 text-center text-slate-500" aria-live="polite">Loading…</main>;
  if (!token || !sessionValidated) return <main className="p-8 text-center"><p className={dark ? 'text-slate-300' : 'text-slate-600'}>{language === 'ar' ? 'سجّل الدخول لإدارة إعلاناتك.' : 'Sign in to manage your listings.'}</p><Link href="/account" className="mt-4 inline-block rounded-xl bg-indigo-600 px-4 py-2 font-semibold text-white">{language === 'ar' ? 'تسجيل الدخول' : 'Sign In'}</Link></main>;
  if (loading) return <main className="p-8 text-center text-slate-500" aria-live="polite">Loading listing…</main>;
  if (error && listingId && !form.make) return <RouteErrorState message={error} onRetry={() => router.refresh()} />;

  return <main className="mx-auto max-w-5xl p-4 md:p-8">
    <Link href="/my-listings" className="text-sm font-semibold text-indigo-600">← {language === 'ar' ? 'إعلاناتي' : 'My Listings'}</Link>
    <h1 className={`mb-6 mt-2 text-3xl font-bold ${dark ? 'text-white' : 'text-slate-900'}`}>{listingId ? (language === 'ar' ? 'تعديل الإعلان' : 'Edit Listing') : (language === 'ar' ? 'إضافة إعلان' : 'Create Listing')}</h1>
    <form onSubmit={submit} className={`space-y-6 rounded-3xl border p-4 shadow-sm md:p-6 ${dark ? 'border-slate-700 bg-slate-900' : 'border-slate-200 bg-white'}`}>
      {error ? <p role="alert" className="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}{notice ? <p aria-live="polite" className="rounded-xl bg-sky-50 p-3 text-sm text-sky-700">{notice}</p> : null}
      <UploadRecovery key={`${token}:${listingId ?? 'new'}`} token={token} language={language} dark={dark} disabled={uploading || submitting}
        imageCount={new Set([form.image, ...form.galleryImages].filter(Boolean)).size} videoCount={form.videoUrls.length}
        onAdd={(kind, url, assetId) => setForm((current) => addRecoveredMedia(current, kind, url, assetId))} />
      <section><h2 className={`mb-3 font-semibold ${dark ? 'text-white' : 'text-slate-900'}`}>Required information</h2><div className="grid gap-4 sm:grid-cols-2">
        <label className={dark ? 'text-slate-200' : 'text-slate-700'}>Make *<input list="listing-makes" value={form.make} onChange={(event) => update('make', event.target.value)} className={fieldClass} required/><datalist id="listing-makes">{makes.map((make) => <option key={make} value={make}/>)}</datalist></label>
        <label className={dark ? 'text-slate-200' : 'text-slate-700'}>Model *<input list="listing-models" value={form.model} onChange={(event) => update('model', event.target.value)} className={fieldClass} required/><datalist id="listing-models">{models.map((model) => <option key={model} value={model}/>)}</datalist></label>
        <label className={dark ? 'text-slate-200' : 'text-slate-700'}>Year *<input type="number" min="1900" max={new Date().getFullYear() + 2} value={form.year} onChange={(event) => update('year', event.target.value)} className={fieldClass} required/></label>
        <label className={dark ? 'text-slate-200' : 'text-slate-700'}>Price *<span className="flex gap-2"><input type="number" min="0" value={form.price} onChange={(event) => update('price', event.target.value)} className={fieldClass} required/><select aria-label="Currency" value={form.currency} onChange={(event) => update('currency', event.target.value as CurrencyCode)} className="rounded-xl border px-2">{CURRENCIES.map((currency) => <option key={currency}>{currency}</option>)}</select></span></label>
      </div></section>
      <section><h2 className={`mb-3 font-semibold ${dark ? 'text-white' : 'text-slate-900'}`}>Vehicle specifications</h2><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <input aria-label="Body style" placeholder="Body style" value={form.bodyStyle} onChange={(event) => update('bodyStyle', event.target.value)} className={fieldClass}/><input aria-label="Horsepower" type="number" min="0" placeholder="Horsepower" value={form.horsepower} onChange={(event) => update('horsepower', event.target.value)} className={fieldClass}/><label><span className="sr-only">Engine</span><input list="listing-engines" placeholder="Engine" value={form.engine} onChange={(event) => update('engine', event.target.value)} className={fieldClass}/><datalist id="listing-engines">{engines.map((engine) => <option key={engine} value={engine}/>)}</datalist></label><input aria-label="Fuel economy" placeholder="Fuel economy" value={form.fuelEconomy} onChange={(event) => update('fuelEconomy', event.target.value)} className={fieldClass}/><input aria-label="Odometer" type="number" min="0" placeholder="Odometer (km)" value={form.odometer} onChange={(event) => update('odometer', event.target.value)} className={fieldClass}/><input aria-label="Primary image URL" type="url" placeholder="Primary image URL" value={form.image} onChange={(event) => update('image', event.target.value)} className={fieldClass}/>
      </div></section>
      <section><h2 className={`mb-3 font-semibold ${dark ? 'text-white' : 'text-slate-900'}`}>Additional details</h2><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <select aria-label="Category" value={form.category} onChange={(event) => update('category', event.target.value as VehicleCategory)} className={fieldClass}>{CATEGORIES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><select aria-label="Condition" value={form.condition} onChange={(event) => update('condition', event.target.value as VehicleCondition)} className={fieldClass}>{CONDITIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><select aria-label="Transmission" value={form.transmission} onChange={(event) => update('transmission', event.target.value as TransmissionType | '')} className={fieldClass}>{TRANSMISSIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><select aria-label="Fuel type" value={form.fuelType} onChange={(event) => update('fuelType', event.target.value as FuelType | '')} className={fieldClass}>{FUELS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><select aria-label="Regional specification" value={form.regionalSpec} onChange={(event) => update('regionalSpec', event.target.value as RegionalSpec | '')} className={fieldClass}>{REGIONAL_SPECS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><select aria-label="Payment type" value={form.paymentType} onChange={(event) => update('paymentType', event.target.value as PaymentType)} className={fieldClass}>{PAYMENTS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select><input aria-label="Trim" placeholder="Trim" value={form.trim} onChange={(event) => update('trim', event.target.value)} className={fieldClass}/><input aria-label="Exterior color" placeholder="Exterior color" value={form.exteriorColor} onChange={(event) => update('exteriorColor', event.target.value)} className={fieldClass}/><input aria-label="Interior color" placeholder="Interior color" value={form.interiorColor} onChange={(event) => update('interiorColor', event.target.value)} className={fieldClass}/><input aria-label="City" placeholder="City" value={form.city} onChange={(event) => update('city', event.target.value)} className={fieldClass}/><input aria-label="Neighborhood" placeholder="Neighborhood" value={form.neighborhood} onChange={(event) => update('neighborhood', event.target.value)} className={fieldClass}/>
      </div></section>
      <textarea aria-label="Description" placeholder="Description" value={form.description} onChange={(event) => update('description', event.target.value)} className={`${fieldClass} min-h-32`}/>
      <section className={`space-y-4 rounded-2xl p-4 ${dark ? 'bg-slate-800' : 'bg-slate-50'}`}><div className="flex flex-wrap gap-3"><label className="cursor-pointer rounded-xl border border-dashed border-slate-400 px-4 py-2 text-sm font-semibold">Upload images ({form.galleryImages.length}/12)<input className="hidden" type="file" accept=".png,.jpg,.jpeg,.gif,.webp" multiple disabled={uploading || submitting} onChange={(event) => void uploadImages(event.target.files)}/></label><label className="cursor-pointer rounded-xl border border-dashed border-slate-400 px-4 py-2 text-sm font-semibold">Upload videos ({form.videoUrls.length}/2)<input className="hidden" type="file" accept=".mp4,.mov,.avi,.mkv,.webm" multiple disabled={uploading || submitting} onChange={(event) => void uploadVideos(event.target.files)}/></label><label className="cursor-pointer rounded-xl border border-dashed border-slate-400 px-4 py-2 text-sm font-semibold">AI image helper<input className="hidden" type="file" accept="image/*" onChange={(event) => void analyzeImage(event.target.files?.[0])}/></label><button type="button" onClick={() => void estimatePrice()} disabled={assisting} className="rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white">Estimate price</button></div>
        <div className="grid gap-3 sm:grid-cols-3 md:grid-cols-4">{form.galleryImages.map((url, index) => <div key={`${url}-${index}`} className="relative"><Image unoptimized src={url} alt={`Listing image ${index + 1}`} width={320} height={180} className="h-32 w-full rounded-xl object-cover"/><button type="button" aria-label={`Remove image ${index + 1}`} onClick={() => setForm((current) => { const galleryImages = current.galleryImages.filter((_, itemIndex) => itemIndex !== index); return { ...current, galleryImages, image: current.image === url ? galleryImages[0] ?? '' : current.image }; })} className="absolute right-2 top-2 rounded-full bg-white px-2 py-1 text-rose-600">×</button></div>)}</div>
        <div className="grid gap-3 sm:grid-cols-2">{form.videoUrls.map((url, index) => <div key={`${url}-${index}`} className="relative"><video src={url} controls className="h-40 w-full rounded-xl object-cover"/><button type="button" aria-label={`Remove video ${index + 1}`} onClick={() => setForm((current) => ({ ...current, videoUrls: current.videoUrls.filter((_, itemIndex) => itemIndex !== index) }))} className="absolute right-2 top-2 rounded-full bg-white px-2 py-1 text-rose-600">×</button></div>)}</div>
        {vision?.highlights?.length ? <div className={dark ? 'text-slate-200' : 'text-slate-700'}><p className="font-semibold">Vision insights</p>{vision.highlights.map((highlight) => <p key={highlight}>• {highlight}</p>)}</div> : null}
      </section>
      <button disabled={submitting || uploading || assisting} className="w-full rounded-2xl bg-emerald-600 py-3 font-semibold text-white disabled:opacity-60">{submitting ? 'Saving…' : listingId ? 'Save Changes' : 'Publish Listing'}</button>
    </form>
  </main>;
}
