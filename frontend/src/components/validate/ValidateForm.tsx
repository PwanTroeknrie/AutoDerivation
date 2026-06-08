import { useState, type FormEvent } from "react";
import Field from "../shared/Field";
import Button from "../shared/Button";
import type { ValidatePayload } from "../../types";

interface ValidateFormProps {
  onSubmit: (payload: ValidatePayload) => Promise<unknown>;
  loading: boolean;
}

export default function ValidateForm({ onSubmit, loading }: ValidateFormProps) {
  const [word, setWord] = useState("");
  const [pos, setPos] = useState("noun");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!word.trim()) return;
    onSubmit({ word: word.trim(), pos });
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="panel glass min-h-[104px] grid grid-cols-[1fr_120px_112px] gap-3 items-end p-4 max-[820px]:grid-cols-1"
    >
      <Field label="检测词根" htmlFor="validate-word">
        <input
          id="validate-word"
          value={word}
          onChange={(e) => setWord(e.target.value)}
          placeholder="例如 kapi"
          autoComplete="off"
          className="input-brutal"
        />
      </Field>
      <Field label="词性" htmlFor="validate-pos">
        <select
          id="validate-pos"
          value={pos}
          onChange={(e) => setPos(e.target.value)}
          className="input-brutal"
        >
          <option value="noun">名词</option>
          <option value="verb">动词</option>
        </select>
      </Field>
      <Button type="submit" disabled={loading}>
        {loading ? "检测中" : "检测"}
      </Button>
    </form>
  );
}
