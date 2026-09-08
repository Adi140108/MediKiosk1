import React, { useState } from 'react';
import { User, Phone, Sparkles, Users, ArrowRight, ShieldCheck } from 'lucide-react';

export default function Step3PatientInfo({ initialData = {}, onNext }) {
  const [formData, setFormData] = useState({
    name: initialData.name || '',
    age: initialData.age || '',
    gender: initialData.gender || 'Female',
    phone: initialData.phone || '',
    abhaId: initialData.abhaId || '',
    isAttendant: initialData.isAttendant || false,
    attendantName: initialData.attendantName || '',
    attendantRelation: initialData.attendantRelation || 'Family Member'
  });

  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};
    if (!formData.name.trim()) newErrors.name = "Full name is required";
    if (!formData.age || isNaN(formData.age) || Number(formData.age) < 0 || Number(formData.age) > 120) {
      newErrors.age = "Valid age (0–120) is required";
    }
    if (!formData.phone.trim() || formData.phone.length < 10) {
      newErrors.phone = "10-digit mobile number required";
    }
    if (formData.isAttendant && !formData.attendantName.trim()) {
      newErrors.attendantName = "Attendant name is required";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validate()) {
      onNext(formData);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6">
      <div className="bg-white/95 backdrop-blur-md rounded-3xl p-6 sm:p-10 lg:p-12 border border-slate-200/80 shadow-lg">
        
        {/* Header */}
        <div className="text-center max-w-xl mx-auto mb-8 sm:mb-10">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-emerald-100/90 text-emerald-800 text-xs font-bold mb-3 shadow-2xs">
            <User className="w-3.5 h-3.5 text-emerald-700" />
            <span>Step 3: Identification</span>
          </div>
          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-serif font-bold text-[#0d382d] tracking-tight">
            Patient Registration &amp; ABHA ID
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 mt-1.5 font-normal">
            Please provide your details for the clinical OPD record.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          
          {/* SECTION 1: Personal Details */}
          <div className="space-y-5">
            <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-900/80 pb-2 border-b border-slate-100 flex items-center gap-2">
              <User className="w-3.5 h-3.5 text-emerald-800" />
              <span>Personal Information</span>
            </h3>

            {/* Full Name - Spacious Full Row */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Full Name *
              </label>
              <input
                type="text"
                placeholder="e.g. Ananya Sharma"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-3.5 rounded-2xl border border-slate-300 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100 outline-none text-slate-800 text-sm sm:text-base transition-all bg-white"
              />
              {errors.name && <p className="text-xs text-red-500 font-medium mt-1.5">{errors.name}</p>}
            </div>

            {/* Age & Gender - Clean 2-Column Split */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 sm:gap-6">
              {/* Age */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Age (Years) *
                </label>
                <input
                  type="number"
                  placeholder="e.g. 28"
                  value={formData.age}
                  onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                  className="w-full px-4 py-3.5 rounded-2xl border border-slate-300 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100 outline-none text-slate-800 text-sm sm:text-base transition-all bg-white"
                />
                {errors.age && <p className="text-xs text-red-500 font-medium mt-1.5">{errors.age}</p>}
              </div>

              {/* Gender Segmented Selection */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Gender *
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {['Female', 'Male', 'Other'].map((g) => (
                    <button
                      key={g}
                      type="button"
                      onClick={() => setFormData({ ...formData, gender: g })}
                      className={`py-3.5 px-3 rounded-2xl text-xs sm:text-sm font-bold transition-all cursor-pointer border ${
                        formData.gender === g
                          ? 'bg-[#0d382d] text-white border-[#0d382d] shadow-xs scale-[1.02]'
                          : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* SECTION 2: Contact & ABHA ID */}
          <div className="space-y-5 pt-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-900/80 pb-2 border-b border-slate-100 flex items-center gap-2">
              <Phone className="w-3.5 h-3.5 text-emerald-800" />
              <span>Contact &amp; ABDM Identification</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 sm:gap-6">
              {/* Mobile Number */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Mobile Number (for SMS token) *
                </label>
                <div className="relative">
                  <input
                    type="tel"
                    placeholder="10-digit mobile number"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="w-full px-4 py-3.5 rounded-2xl border border-slate-300 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100 outline-none text-slate-800 text-sm sm:text-base transition-all bg-white"
                  />
                </div>
                {errors.phone ? (
                  <p className="text-xs text-red-500 font-medium mt-1.5">{errors.phone}</p>
                ) : (
                  <p className="text-[11px] text-slate-500 mt-1">Your OPD queue number will be sent here</p>
                )}
              </div>

              {/* ABHA / Health ID */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center justify-between">
                  <span>ABHA / Health ID (Optional)</span>
                  <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                    <ShieldCheck className="w-3 h-3" />
                    ABDM Enabled
                  </span>
                </label>
                <input
                  type="text"
                  placeholder="e.g. 14-digit number or name@abdm"
                  value={formData.abhaId}
                  onChange={(e) => setFormData({ ...formData, abhaId: e.target.value })}
                  className="w-full px-4 py-3.5 rounded-2xl border border-slate-300 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100 outline-none text-slate-800 text-sm sm:text-base transition-all bg-white"
                />
                <p className="text-[11px] text-slate-500 mt-1">Leave blank to auto-generate a provisional token</p>
              </div>
            </div>
          </div>

          {/* SECTION 3: Attendant Mode */}
          <div className="pt-2">
            <div className={`p-5 sm:p-6 rounded-2xl border transition-all ${
              formData.isAttendant ? 'bg-emerald-50/50 border-emerald-200' : 'bg-slate-50/70 border-slate-200'
            }`}>
              <label className="flex items-start sm:items-center gap-3.5 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={formData.isAttendant}
                  onChange={(e) => setFormData({ ...formData, isAttendant: e.target.checked })}
                  className="w-5 h-5 rounded-md border-slate-300 text-[#0d382d] focus:ring-emerald-500 accent-[#0d382d] cursor-pointer mt-0.5 sm:mt-0"
                />
                <div>
                  <span className="text-sm font-bold text-slate-900 block">
                    Someone else is helping me check in (Attendant Mode)
                  </span>
                  <span className="text-xs text-slate-500 block mt-0.5">
                    Check this if a family member, caregiver, or hospital staff is completing intake on behalf of the patient.
                  </span>
                </div>
              </label>

              {formData.isAttendant && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-5 pt-4 border-t border-emerald-100">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                      Attendant Name *
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Rajesh Sharma"
                      value={formData.attendantName}
                      onChange={(e) => setFormData({ ...formData, attendantName: e.target.value })}
                      className="w-full px-3.5 py-3 rounded-xl border border-slate-300 bg-white text-sm outline-none focus:border-emerald-600 focus:ring-1 focus:ring-emerald-100"
                    />
                    {errors.attendantName && (
                      <p className="text-xs text-red-500 font-medium mt-1">{errors.attendantName}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                      Relationship to Patient
                    </label>
                    <select
                      value={formData.attendantRelation}
                      onChange={(e) => setFormData({ ...formData, attendantRelation: e.target.value })}
                      className="w-full px-3.5 py-3 rounded-xl border border-slate-300 bg-white text-sm outline-none focus:border-emerald-600 focus:ring-1 focus:ring-emerald-100 cursor-pointer"
                    >
                      <option value="Family Member">Family Member / Relative</option>
                      <option value="Guardian">Parent / Guardian</option>
                      <option value="Caregiver">Caregiver / Nurse</option>
                      <option value="Hospital Staff">Hospital Helpdesk Staff</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Submit Action */}
          <div className="flex justify-end pt-4">
            <button
              type="submit"
              className="inline-flex items-center justify-center gap-2.5 px-9 py-4 rounded-xl bg-[#0d382d] hover:bg-[#134e3f] text-white font-bold text-sm sm:text-base shadow-md hover:shadow-lg transition-all hover:scale-102 cursor-pointer w-full sm:w-auto"
            >
              <span>Save &amp; Continue</span>
              <ArrowRight className="w-5 h-5" />
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}
