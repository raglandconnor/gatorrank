import type { Metadata } from 'next';
import { Mona_Sans } from 'next/font/google';
import { Provider } from '@/components/ui/provider';
import './globals.css';

const monaSans = Mona_Sans({
  subsets: ['latin'],
  variable: '--font-mona-sans',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'GatorRank',
  description: 'Rank and discover student-made projects at UF.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={monaSans.variable} suppressHydrationWarning>
      <body suppressHydrationWarning>
        <Provider forcedTheme="light" enableSystem={false} defaultTheme="light">
          {children}
        </Provider>
      </body>
    </html>
  );
}
