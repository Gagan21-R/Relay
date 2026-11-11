// A page whose content arrives in a later build phase (Section 12). It says which phase, so nothing looks finished early.
import { useTranslation } from "react-i18next";
import { PageHeader } from "../components/Layout";

export default function Planned({ navKey, pageKey, phase }: { navKey: string; pageKey: string; phase: number }) {
  const { t } = useTranslation();
  return (
    <div>
      <PageHeader title={t(`nav.${navKey}`)} sub={t(`pages.${pageKey}`)} />
      <div className="card grid place-items-center border-dashed p-10 text-center">
        <p className="badge bg-brand-50 text-brand-700">{t("common.comingIn", { phase })}</p>
      </div>
    </div>
  );
}
