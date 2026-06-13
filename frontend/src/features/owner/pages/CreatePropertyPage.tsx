import PropertyForm from "../components/PropertyForm";

export default function CreatePropertyPage() {
  return (
    <div className="space-y-6 animate-slide-up">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight">List New Property</h1>
        <p className="text-text-secondary text-sm mt-1">
          Complete the details below to initialize your student accommodation listing. You will be able to configure media, amenities, and inventory in subsequent steps.
        </p>
      </div>

      {/* Form Wizard Component */}
      <PropertyForm />
    </div>
  );
}
