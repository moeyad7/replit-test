import { SettingsIcon, HelpIcon } from "../ui/icons";

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 z-10">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center space-x-3">
          <div className="text-primary">
            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M10 11h-4a1 1 0 0 1 -1 -1v-3a1 1 0 0 1 1 -1h3.5a1 1 0 0 1 1 1v.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M13 7.5v-3a1 1 0 0 1 1 -1h3.5a1 1 0 0 1 1 1v3a1 1 0 0 1 -1 1h-3.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M8 13v-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M13.4 19h-5.4a2 2 0 0 1 -2 -2v-6h6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M13.5 19l4 -6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M16 19h3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h1 className="text-xl font-semibold text-gray-800">Loyalty Insights</h1>
        </div>
        <div className="flex items-center space-x-4">
          <button className="text-gray-500 hover:text-gray-700">
            <SettingsIcon size={20} />
          </button>
          <button className="text-gray-500 hover:text-gray-700">
            <HelpIcon size={20} />
          </button>
          <div className="relative">
            <button className="flex items-center">
              <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 font-medium">
                JD
              </div>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
