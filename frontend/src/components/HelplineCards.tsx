export interface Helpline {
  name: string;
  numbers: string;
  description: string;
  tone: 'red' | 'blue' | 'emerald';
}

const HELPLINES: Helpline[] = [
  {
    name: 'Tele-MANAS National Helpline',
    numbers: '14416 / 1-800-891-4416',
    description: 'Government of India · Toll-free 24/7 support in 20 languages',
    tone: 'blue',
  },
  {
    name: 'Emergency Services',
    numbers: '112',
    description: 'National emergency response (Medical, Police, Fire)',
    tone: 'red',
  },
  {
    name: 'Vandrevala Foundation Helpline',
    numbers: '+91 9999 666 555',
    description: 'Free 24x7x365 counseling — call or WhatsApp',
    tone: 'emerald',
  },
];

const TONE_STYLES = {
  red: 'bg-red-50 border-red-200 text-red-900',
  blue: 'bg-blue-50 border-blue-200 text-blue-900',
  emerald: 'bg-emerald-50 border-emerald-200 text-emerald-900',
};

export default function HelplineCards() {
  return (
    <div className="space-y-3" role="list" aria-label="Crisis helpline numbers">
      {HELPLINES.map((line) => (
        <div key={line.name} className={`p-4 rounded-xl border ${TONE_STYLES[line.tone]}`} role="listitem">
          <div className="font-semibold">{line.name}</div>
          <a href={`tel:${line.numbers.split('/')[0].replace(/[^+\d]/g, '')}`} className="block text-2xl font-black my-0.5 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 rounded">
            {line.numbers}
          </a>
          <div className="text-xs opacity-90">{line.description}</div>
        </div>
      ))}
    </div>
  );
}
