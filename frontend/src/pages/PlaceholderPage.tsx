import { ExternalLink } from "lucide-react";
import Masthead from "../components/shared/Masthead";
import PaneHead from "../components/shared/PaneHead";
import Button from "../components/shared/Button";
import Chip from "../components/shared/Chip";

interface PlaceholderPageProps {
  title: string;
  label: string;
  description: string;
}

export default function PlaceholderPage({ title, label, description }: PlaceholderPageProps) {
  return (
    <main className="w-[min(1180px,calc(100%-32px))] mx-auto py-8 max-[820px]:w-[min(100%-20px,680px)]">
      <Masthead eyebrow="Coming Module" title={title} markVariant={3} />
      <section className="panel glass p-4 min-h-[420px] grid content-start gap-4">
        <PaneHead title={label} status="Placeholder" />
        <div className="border border-ink bg-white p-5 grid gap-3 max-w-[760px]">
          <div className="flex flex-wrap gap-[6px]">
            <Chip text="planned" />
            <Chip text="navigation ready" />
          </div>
          <p className="m-0 text-[20px] leading-[1.45]">{description}</p>
          <div className="flex flex-wrap gap-2">
            <Button as="a" href="/" variant="ghost">Back Home</Button>
            <Button as="a" href="https://github.com/" target="_blank" rel="noreferrer">
              <ExternalLink size={16} />
              Project Home
            </Button>
          </div>
        </div>
      </section>
    </main>
  );
}
