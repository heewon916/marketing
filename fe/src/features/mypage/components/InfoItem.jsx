import { accountInfoCardStyles } from './accountInfoCardStyles';

export default function InfoItem({ label, value }) {
  return (
    <div className={accountInfoCardStyles.section}>
      <dt className={accountInfoCardStyles.label}>
        {label}
      </dt>

      <dd className={accountInfoCardStyles.value}>
        {value}
      </dd>
    </div>
  );
}
