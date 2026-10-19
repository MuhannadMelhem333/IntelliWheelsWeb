import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Script from "next/script";
import "./globals.css";

const GA_ID = "G-T959BS302R";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const SITE_URL = "https://intelliwheels.co";
const SITE_NAME = "IntelliWheels";
const SITE_DESCRIPTION =
  "Jordan's smartest AI-powered automotive marketplace. Find your perfect car with AI search, vision recognition, fair price estimation, and verified dealers across Jordan and the GCC.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  applicationName: SITE_NAME,
  title: {
    default: "IntelliWheels – AI-Powered Car Marketplace | Jordan & GCC",
    template: "%s | IntelliWheels",
  },
  description: SITE_DESCRIPTION,
  keywords: [
    "cars Jordan",
    "سيارات الأردن",
    "used cars Amman",
    "سيارات مستعملة عمان",
    "AI car marketplace",
    "car price estimation",
    "تقدير اسعار السيارات",
    "verified dealers Jordan",
    "وكلاء سيارات الأردن",
    "buy car Jordan",
    "sell car Jordan",
    "GCC cars",
    "IntelliWheels",
    "انتلي ويلز",
  ],
  authors: [{ name: "IntelliWheels Team" }],
  creator: "IntelliWheels",
  publisher: "IntelliWheels",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-image-preview': 'large',
      'max-snippet': -1,
      'max-video-preview': -1,
    },
  },
  manifest: '/manifest.webmanifest',
  category: 'automotive',
  openGraph: {
    type: "website",
    locale: "en_US",
    alternateLocale: "ar_JO",
    url: SITE_URL,
    siteName: SITE_NAME,
    title: "IntelliWheels – AI-Powered Car Marketplace | Jordan & GCC",
    description: SITE_DESCRIPTION,
    images: [
      {
        url: "/IntelliWheels_Logo_Dark.png",
        width: 1200,
        height: 630,
        alt: "IntelliWheels – AI-Powered Automotive Marketplace",
      },
    ],
  },
  icons: {
    icon: [
      { url: '/IntelliWheels_Logo_Dark.png', sizes: '32x32', type: 'image/png' },
      { url: '/IntelliWheels_Logo_Dark.png', sizes: '192x192', type: 'image/png' },
    ],
    shortcut: '/IntelliWheels_Logo_Dark.png',
    apple: [
      { url: '/IntelliWheels_Logo_Dark.png', sizes: '180x180', type: 'image/png' },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'IntelliWheels - AI-Powered Car Marketplace | Jordan & GCC',
    description: SITE_DESCRIPTION,
    images: ['/IntelliWheels_Logo_Dark.png'],
  },
};

// JSON-LD structured data for SEO
const jsonLd = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${SITE_URL}/#organization`,
      name: SITE_NAME,
      url: SITE_URL,
      logo: {
        "@type": "ImageObject",
        url: `${SITE_URL}/IntelliWheels_Logo_Dark.png`,
      },
      description: SITE_DESCRIPTION,
      foundingDate: "2025",
      founders: [
        { "@type": "Person", name: "Hamza Jabari" },
      ],
      address: {
        "@type": "PostalAddress",
        addressLocality: "Amman",
        addressCountry: "JO",
      },
      contactPoint: {
        "@type": "ContactPoint",
        email: "intelliwheels03@gmail.com",
        telephone: "+962-77-738-1408",
        contactType: "customer service",
        availableLanguage: ["English", "Arabic"],
      },
      sameAs: [
        "https://www.instagram.com/intelli_wheels1/",
      ],
    },
    {
      "@type": "WebSite",
      "@id": `${SITE_URL}/#website`,
      url: SITE_URL,
      name: SITE_NAME,
      description: SITE_DESCRIPTION,
      publisher: { "@id": `${SITE_URL}/#organization` },
      inLanguage: ["en", "ar"],
      potentialAction: {
        "@type": "SearchAction",
        target: {
          "@type": "EntryPoint",
          urlTemplate: `${SITE_URL}/?search={search_term_string}`,
        },
        "query-input": "required name=search_term_string",
      },
    },
    {
      "@type": "WebApplication",
      name: SITE_NAME,
      url: SITE_URL,
      applicationCategory: "BusinessApplication",
      operatingSystem: "Web",
      offers: {
        "@type": "Offer",
        price: "0",
        priceCurrency: "JOD",
        description: "Free to browse and list cars",
      },
      featureList: [
        "AI-powered car search",
        "Vision recognition for vehicles",
        "Fair market price estimation",
        "Verified dealer network",
        "Bilingual Arabic/English interface",
        "Multi-currency support",
      ],
    },
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {/* Google Analytics 4 */}
        <Script
          src={`https://www.googletagmanager.com/gtag/js?id=${GA_ID}`}
          strategy="afterInteractive"
        />
        <Script id="ga4-init" strategy="afterInteractive">
          {`
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            gtag('config', '${GA_ID}', {
              page_path: window.location.pathname,
            });
          `}
        </Script>
        {children}
      </body>
    </html>
  );
}
